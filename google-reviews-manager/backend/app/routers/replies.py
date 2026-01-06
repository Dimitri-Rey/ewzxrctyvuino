"""Reply management routes with manual approval."""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db, Review, Location, PendingReply, PendingReplyStatus
from app.services.google_business import get_google_business_service
from app.services.template_engine import get_template_engine
from app.schemas.replies import (
    SuggestReplyResponse,
    PendingReplyResponse,
    ApproveReplyRequest,
    RejectReplyRequest,
    EditReplyRequest
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/replies", tags=["replies"])


@router.post("/reviews/{review_id}/suggest-reply", response_model=SuggestReplyResponse)
async def suggest_reply(
    review_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a suggested reply for a review based on templates.
    
    Args:
        review_id: The review ID
        db: Database session
        
    Returns:
        SuggestReplyResponse: Suggested reply text and template info
    """
    try:
        # Get review
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=404,
                detail=f"Review with id {review_id} not found"
            )
        
        # Check if review already has a reply
        if review.reply:
            raise HTTPException(
                status_code=400,
                detail="This review already has a reply"
            )
        
        # Check if there's already a pending reply
        existing_pending = db.query(PendingReply).filter(
            PendingReply.review_id == review_id
        ).first()
        
        if existing_pending and existing_pending.status == PendingReplyStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="A pending reply already exists for this review"
            )
        
        # Get location
        location = db.query(Location).filter(Location.id == review.location_id).first()
        if not location:
            raise HTTPException(
                status_code=404,
                detail=f"Location for review {review_id} not found"
            )
        
        # Generate reply using template engine
        engine = get_template_engine()
        suggested_reply = engine.generate_reply(review, location.name, db=db)
        
        if not suggested_reply:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate suggested reply"
            )
        
        # Get the template used
        template = engine.suggest_template(review, location.name, db)
        template_id = template.id if template else None
        template_name = template.name if template else None
        
        # Create pending reply
        if existing_pending:
            # Update existing rejected reply
            existing_pending.suggested_reply = suggested_reply
            existing_pending.status = PendingReplyStatus.PENDING
            existing_pending.processed_at = None
            db.commit()
            db.refresh(existing_pending)
            pending_reply = existing_pending
        else:
            # Create new pending reply
            pending_reply = PendingReply(
                review_id=review_id,
                suggested_reply=suggested_reply,
                status=PendingReplyStatus.PENDING
            )
            db.add(pending_reply)
            db.commit()
            db.refresh(pending_reply)
        
        return SuggestReplyResponse(
            suggested_reply=suggested_reply,
            template_id=template_id,
            template_name=template_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error suggesting reply: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to suggest reply: {str(e)}"
        )


@router.get("/pending", response_model=List[PendingReplyResponse])
async def list_pending_replies(
    db: Session = Depends(get_db)
):
    """
    List all pending replies awaiting approval.
    
    Args:
        db: Database session
        
    Returns:
        List[PendingReplyResponse]: List of pending replies
    """
    try:
        pending_replies = db.query(PendingReply).filter(
            PendingReply.status == PendingReplyStatus.PENDING
        ).order_by(PendingReply.created_at.desc()).all()
        
        result = []
        for pending in pending_replies:
            review = db.query(Review).filter(Review.id == pending.review_id).first()
            if review:
                location = db.query(Location).filter(Location.id == review.location_id).first()
                result.append(PendingReplyResponse(
                    id=pending.id,
                    review_id=pending.review_id,
                    suggested_reply=pending.suggested_reply,
                    status=pending.status.value,
                    created_at=pending.created_at,
                    processed_at=pending.processed_at,
                    review_author_name=review.author_name,
                    review_rating=review.rating,
                    review_comment=review.comment,
                    location_name=location.name if location else "Unknown"
                ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing pending replies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list pending replies: {str(e)}"
        )


@router.post("/{pending_reply_id}/approve", response_model=PendingReplyResponse)
async def approve_reply(
    pending_reply_id: int,
    approval_data: ApproveReplyRequest,
    db: Session = Depends(get_db)
):
    """
    Approve and send a pending reply to Google.
    
    Args:
        pending_reply_id: The pending reply ID
        approval_data: Optional edited reply text
        db: Database session
        
    Returns:
        PendingReplyResponse: Updated pending reply
    """
    try:
        # Get pending reply
        pending_reply = db.query(PendingReply).filter(
            PendingReply.id == pending_reply_id
        ).first()
        
        if not pending_reply:
            raise HTTPException(
                status_code=404,
                detail=f"Pending reply with id {pending_reply_id} not found"
            )
        
        if pending_reply.status != PendingReplyStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Pending reply is not in pending status (current: {pending_reply.status.value})"
            )
        
        # Get review and location
        review = db.query(Review).filter(Review.id == pending_reply.review_id).first()
        if not review:
            raise HTTPException(
                status_code=404,
                detail=f"Review for pending reply {pending_reply_id} not found"
            )
        
        location = db.query(Location).filter(Location.id == review.location_id).first()
        if not location:
            raise HTTPException(
                status_code=404,
                detail=f"Location for review {review.id} not found"
            )
        
        # Use edited reply if provided, otherwise use suggested reply
        reply_text = approval_data.edited_reply if approval_data.edited_reply else pending_reply.suggested_reply
        
        # Send reply via Google API
        business_service = get_google_business_service()
        business_service.reply_to_review(
            location_id=location.id,
            review_id=review.review_id,
            reply_text=reply_text,
            db=db
        )
        
        # Update pending reply status
        pending_reply.status = PendingReplyStatus.APPROVED
        pending_reply.processed_at = datetime.utcnow()
        if approval_data.edited_reply:
            pending_reply.suggested_reply = approval_data.edited_reply
        db.commit()
        db.refresh(pending_reply)
        
        return PendingReplyResponse(
            id=pending_reply.id,
            review_id=pending_reply.review_id,
            suggested_reply=pending_reply.suggested_reply,
            status=pending_reply.status.value,
            created_at=pending_reply.created_at,
            processed_at=pending_reply.processed_at,
            review_author_name=review.author_name,
            review_rating=review.rating,
            review_comment=review.comment,
            location_name=location.name
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving reply: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve reply: {str(e)}"
        )


@router.post("/{pending_reply_id}/reject", response_model=PendingReplyResponse)
async def reject_reply(
    pending_reply_id: int,
    rejection_data: RejectReplyRequest,
    db: Session = Depends(get_db)
):
    """
    Reject a pending reply suggestion.
    
    Args:
        pending_reply_id: The pending reply ID
        rejection_data: Optional rejection reason
        db: Database session
        
    Returns:
        PendingReplyResponse: Updated pending reply
    """
    try:
        # Get pending reply
        pending_reply = db.query(PendingReply).filter(
            PendingReply.id == pending_reply_id
        ).first()
        
        if not pending_reply:
            raise HTTPException(
                status_code=404,
                detail=f"Pending reply with id {pending_reply_id} not found"
            )
        
        if pending_reply.status != PendingReplyStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Pending reply is not in pending status (current: {pending_reply.status.value})"
            )
        
        # Update status
        pending_reply.status = PendingReplyStatus.REJECTED
        pending_reply.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(pending_reply)
        
        # Get review and location for response
        review = db.query(Review).filter(Review.id == pending_reply.review_id).first()
        location = db.query(Location).filter(Location.id == review.location_id).first() if review else None
        
        return PendingReplyResponse(
            id=pending_reply.id,
            review_id=pending_reply.review_id,
            suggested_reply=pending_reply.suggested_reply,
            status=pending_reply.status.value,
            created_at=pending_reply.created_at,
            processed_at=pending_reply.processed_at,
            review_author_name=review.author_name if review else "Unknown",
            review_rating=review.rating if review else 0,
            review_comment=review.comment if review else None,
            location_name=location.name if location else "Unknown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting reply: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject reply: {str(e)}"
        )


@router.post("/{pending_reply_id}/edit", response_model=PendingReplyResponse)
async def edit_pending_reply(
    pending_reply_id: int,
    edit_data: EditReplyRequest,
    db: Session = Depends(get_db)
):
    """
    Edit a pending reply before approval.
    
    Args:
        pending_reply_id: The pending reply ID
        edit_data: New reply text
        db: Database session
        
    Returns:
        PendingReplyResponse: Updated pending reply
    """
    try:
        # Get pending reply
        pending_reply = db.query(PendingReply).filter(
            PendingReply.id == pending_reply_id
        ).first()
        
        if not pending_reply:
            raise HTTPException(
                status_code=404,
                detail=f"Pending reply with id {pending_reply_id} not found"
            )
        
        if pending_reply.status != PendingReplyStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot edit reply that is not in pending status (current: {pending_reply.status.value})"
            )
        
        # Update suggested reply
        pending_reply.suggested_reply = edit_data.suggested_reply
        db.commit()
        db.refresh(pending_reply)
        
        # Get review and location for response
        review = db.query(Review).filter(Review.id == pending_reply.review_id).first()
        location = db.query(Location).filter(Location.id == review.location_id).first() if review else None
        
        return PendingReplyResponse(
            id=pending_reply.id,
            review_id=pending_reply.review_id,
            suggested_reply=pending_reply.suggested_reply,
            status=pending_reply.status.value,
            created_at=pending_reply.created_at,
            processed_at=pending_reply.processed_at,
            review_author_name=review.author_name if review else "Unknown",
            review_rating=review.rating if review else 0,
            review_comment=review.comment if review else None,
            location_name=location.name if location else "Unknown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error editing pending reply: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to edit pending reply: {str(e)}"
        )
