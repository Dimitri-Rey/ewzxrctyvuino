"""Pydantic schemas for reply management."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.database import PendingReplyStatus


class SuggestReplyResponse(BaseModel):
    """Schema for suggest reply response."""
    suggested_reply: str
    template_id: Optional[int] = None
    template_name: Optional[str] = None


class PendingReplyBase(BaseModel):
    """Base schema for PendingReply."""
    suggested_reply: str = Field(..., min_length=1)


class PendingReplyCreate(PendingReplyBase):
    """Schema for creating a PendingReply."""
    review_id: int


class PendingReplyUpdate(BaseModel):
    """Schema for updating a PendingReply."""
    suggested_reply: Optional[str] = Field(None, min_length=1)


class PendingReplyResponse(BaseModel):
    """Schema for PendingReply response."""
    id: int
    review_id: int
    suggested_reply: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    # Review information
    review_author_name: str
    review_rating: int
    review_comment: Optional[str] = None
    location_name: str
    
    class Config:
        from_attributes = True


class ApproveReplyRequest(BaseModel):
    """Schema for approving a reply."""
    edited_reply: Optional[str] = Field(None, min_length=1, description="Optional edited version of the reply")


class RejectReplyRequest(BaseModel):
    """Schema for rejecting a reply."""
    reason: Optional[str] = Field(None, description="Optional reason for rejection")


class EditReplyRequest(BaseModel):
    """Schema for editing a pending reply."""
    suggested_reply: str = Field(..., min_length=1)
