"""Pydantic schemas for ReplyTemplate models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ReplyTemplateBase(BaseModel):
    """Base schema for ReplyTemplate."""
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    rating_min: int = Field(..., ge=1, le=5)
    rating_max: int = Field(..., ge=1, le=5)
    is_active: bool = True
    
    @field_validator('rating_max')
    @classmethod
    def validate_rating_range(cls, v, info):
        """Validate that rating_max >= rating_min."""
        if 'rating_min' in info.data and v < info.data['rating_min']:
            raise ValueError('rating_max must be greater than or equal to rating_min')
        return v


class ReplyTemplateCreate(ReplyTemplateBase):
    """Schema for creating a ReplyTemplate."""
    pass


class ReplyTemplateUpdate(BaseModel):
    """Schema for updating a ReplyTemplate."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    rating_min: Optional[int] = Field(None, ge=1, le=5)
    rating_max: Optional[int] = Field(None, ge=1, le=5)
    is_active: Optional[bool] = None


class ReplyTemplateResponse(ReplyTemplateBase):
    """Schema for ReplyTemplate response."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TemplatePreviewRequest(BaseModel):
    """Schema for template preview request."""
    content: str = Field(..., min_length=1)
    author_name: str = Field(default="Jean Dupont")
    location_name: str = Field(default="Mon Établissement")
    rating: int = Field(default=5, ge=1, le=5)


class TemplatePreviewResponse(BaseModel):
    """Schema for template preview response."""
    rendered_content: str
    variables_used: list[str]
    is_valid: bool
