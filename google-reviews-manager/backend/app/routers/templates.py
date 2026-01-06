"""Template management routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db, ReplyTemplate
from app.services.template_engine import get_template_engine
from app.schemas.templates import (
    ReplyTemplateCreate,
    ReplyTemplateUpdate,
    ReplyTemplateResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=List[ReplyTemplateResponse])
async def list_templates(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all reply templates.
    
    Args:
        active_only: If True, only return active templates
        db: Database session
        
    Returns:
        List[ReplyTemplateResponse]: List of all templates
    """
    try:
        query = db.query(ReplyTemplate)
        if active_only:
            query = query.filter(ReplyTemplate.is_active == True)
        templates = query.order_by(ReplyTemplate.rating_min, ReplyTemplate.created_at).all()
        return templates
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.post("", response_model=ReplyTemplateResponse, status_code=201)
async def create_template(
    template_data: ReplyTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new reply template.
    
    Args:
        template_data: Template data
        db: Database session
        
    Returns:
        ReplyTemplateResponse: Created template
    """
    try:
        # Validate template content
        engine = get_template_engine()
        is_valid, variables = engine.validate_template_content(template_data.content)
        
        if not is_valid:
            unknown_vars = [v for v in variables if v not in engine.AVAILABLE_VARIABLES]
            raise HTTPException(
                status_code=400,
                detail=f"Unknown variables in template: {unknown_vars}. Available variables: {list(engine.AVAILABLE_VARIABLES.keys())}"
            )
        
        # Create template
        new_template = ReplyTemplate(
            name=template_data.name,
            content=template_data.content,
            rating_min=template_data.rating_min,
            rating_max=template_data.rating_max,
            is_active=template_data.is_active
        )
        
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        
        return new_template
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/{template_id}", response_model=ReplyTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific template by ID.
    
    Args:
        template_id: The template ID
        db: Database session
        
    Returns:
        ReplyTemplateResponse: Template information
    """
    template = db.query(ReplyTemplate).filter(ReplyTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template with id {template_id} not found"
        )
    
    return template


@router.put("/{template_id}", response_model=ReplyTemplateResponse)
async def update_template(
    template_id: int,
    template_data: ReplyTemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing template.
    
    Args:
        template_id: The template ID
        template_data: Updated template data
        db: Database session
        
    Returns:
        ReplyTemplateResponse: Updated template
    """
    template = db.query(ReplyTemplate).filter(ReplyTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template with id {template_id} not found"
        )
    
    try:
        # Validate content if provided
        if template_data.content is not None:
            engine = get_template_engine()
            is_valid, variables = engine.validate_template_content(template_data.content)
            
            if not is_valid:
                unknown_vars = [v for v in variables if v not in engine.AVAILABLE_VARIABLES]
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown variables in template: {unknown_vars}. Available variables: {list(engine.AVAILABLE_VARIABLES.keys())}"
                )
        
        # Update fields
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        # Validate rating range if both are updated
        if template_data.rating_min is not None and template_data.rating_max is not None:
            if template.rating_max < template.rating_min:
                raise HTTPException(
                    status_code=400,
                    detail="rating_max must be greater than or equal to rating_min"
                )
        
        db.commit()
        db.refresh(template)
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a template.
    
    Args:
        template_id: The template ID
        db: Database session
    """
    template = db.query(ReplyTemplate).filter(ReplyTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template with id {template_id} not found"
        )
    
    try:
        db.delete(template)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete template: {str(e)}"
        )


@router.post("/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    preview_data: TemplatePreviewRequest
):
    """
    Preview a template with test data.
    
    Args:
        preview_data: Template content and test variables
        
    Returns:
        TemplatePreviewResponse: Rendered template and validation info
    """
    try:
        engine = get_template_engine()
        
        # Validate template content
        is_valid, variables = engine.validate_template_content(preview_data.content)
        
        if not is_valid:
            unknown_vars = [v for v in variables if v not in engine.AVAILABLE_VARIABLES]
            raise HTTPException(
                status_code=400,
                detail=f"Unknown variables in template: {unknown_vars}. Available variables: {list(engine.AVAILABLE_VARIABLES.keys())}"
            )
        
        # Render template
        variables_dict = {
            'author_name': preview_data.author_name,
            'location_name': preview_data.location_name,
            'rating': preview_data.rating
        }
        
        rendered_content = engine.render_template(preview_data.content, variables_dict)
        
        return TemplatePreviewResponse(
            rendered_content=rendered_content,
            variables_used=variables,
            is_valid=is_valid
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to preview template: {str(e)}"
        )
