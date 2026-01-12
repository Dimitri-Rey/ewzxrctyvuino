"""Template engine for rendering reply templates."""
from typing import Dict, Any, Optional, Tuple
from app.models.database import Review, ReplyTemplate
from sqlalchemy.orm import Session
import re
import logging

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Engine for rendering and managing reply templates."""
    
    # Variables disponibles dans les templates
    AVAILABLE_VARIABLES = {
        'author_name': 'Nom de l\'auteur de l\'avis',
        'location_name': 'Nom de l\'établissement',
        'rating': 'Note de l\'avis (1-5)'
    }
    
    def render_template(self, template_content: str, variables_dict: Dict[str, Any]) -> str:
        """
        Render a template by replacing variables with actual values.
        
        Args:
            template_content: The template content with variables like {variable_name}
            variables_dict: Dictionary of variable names and their values
            
        Returns:
            str: Rendered template with variables replaced
        """
        try:
            rendered = template_content
            
            # Replace all variables in the format {variable_name}
            for key, value in variables_dict.items():
                placeholder = f"{{{key}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            # Check for any remaining variables that weren't replaced
            remaining_vars = re.findall(r'\{(\w+)\}', rendered)
            if remaining_vars:
                logger.warning(f"Unreplaced variables found in template: {remaining_vars}")
            
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            raise ValueError(f"Failed to render template: {str(e)}")
    
    def suggest_template(
        self,
        review: Review,
        location_name: str,
        db: Session
    ) -> Optional[ReplyTemplate]:
        """
        Suggest the best template for a review based on its rating.
        
        Args:
            review: The Review model instance
            location_name: Name of the location
            db: Database session
            
        Returns:
            Optional[ReplyTemplate]: The suggested template or None if no match
        """
        try:
            # Find active templates that match the rating
            templates = db.query(ReplyTemplate).filter(
                ReplyTemplate.is_active == True,
                ReplyTemplate.rating_min <= review.rating,
                ReplyTemplate.rating_max >= review.rating
            ).order_by(ReplyTemplate.rating_min.desc()).all()
            
            if not templates:
                logger.warning(f"No template found for rating {review.rating}")
                return None
            
            # Return the first matching template (most specific match)
            return templates[0]
            
        except Exception as e:
            logger.error(f"Error suggesting template: {e}")
            return None
    
    def generate_reply(
        self,
        review: Review,
        location_name: str,
        template: Optional[ReplyTemplate] = None,
        db: Optional[Session] = None
    ) -> Optional[str]:
        """
        Generate a reply for a review using a template.
        
        Args:
            review: The Review model instance
            location_name: Name of the location
            template: Optional template to use (if None, will suggest one)
            db: Database session (required if template is None)
            
        Returns:
            Optional[str]: Generated reply text or None if generation failed
        """
        try:
            # Get template if not provided
            if template is None:
                if db is None:
                    raise ValueError("Database session required when template is not provided")
                template = self.suggest_template(review, location_name, db)
            
            if template is None:
                logger.warning(f"No template available for review {review.id}")
                return None
            
            # Prepare variables
            variables = {
                'author_name': review.author_name,
                'location_name': location_name,
                'rating': review.rating
            }
            
            # Render template
            reply = self.render_template(template.content, variables)
            
            return reply
            
        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            return None
    
    def validate_template_content(self, content: str) -> Tuple[bool, list[str]]:
        """
        Validate template content and return list of variables used.
        
        Args:
            content: Template content to validate
            
        Returns:
            tuple: (is_valid, list_of_variables)
        """
        variables = re.findall(r'\{(\w+)\}', content)
        unknown_vars = [v for v in variables if v not in self.AVAILABLE_VARIABLES]
        
        is_valid = len(unknown_vars) == 0
        
        return is_valid, variables


# Singleton instance
_template_engine = None

def get_template_engine() -> TemplateEngine:
    """Get or create the template engine instance."""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine()
    return _template_engine


