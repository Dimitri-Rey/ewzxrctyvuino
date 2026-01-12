"""Pydantic schemas for Location and Review models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LocationBase(BaseModel):
    """Base schema for Location."""
    location_id: str
    name: str
    address: Optional[str] = None


class LocationCreate(LocationBase):
    """Schema for creating a Location."""
    account_id: int


class LocationResponse(LocationBase):
    """Schema for Location response."""
    id: int
    account_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    """Base schema for Review."""
    review_id: str
    author_name: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = None
    reply: Optional[str] = None
    reply_time: Optional[datetime] = None
    created_at: datetime


class ReviewCreate(ReviewBase):
    """Schema for creating a Review."""
    location_id: int


class ReviewResponse(ReviewBase):
    """Schema for Review response."""
    id: int
    location_id: int
    synced_at: datetime
    
    class Config:
        from_attributes = True


class LocationWithReviews(LocationResponse):
    """Schema for Location with its reviews."""
    reviews: list[ReviewResponse] = []


