"""Location and review management routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.database import get_db, Location, Review, Account
from app.services.google_business import get_google_business_service
from app.schemas.reviews import (
    LocationResponse,
    ReviewResponse,
    LocationWithReviews
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=List[LocationResponse])
async def list_locations(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: Session = Depends(get_db)
):
    """
    List all locations from all connected accounts.
    
    Args:
        account_id: Optional account ID to filter locations
        db: Database session
        
    Returns:
        List[LocationResponse]: List of all locations
    """
    try:
        if account_id:
            locations = db.query(Location).filter(Location.account_id == account_id).all()
        else:
            locations = db.query(Location).all()
        
        return locations
    except Exception as e:
        logger.error(f"Error listing locations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list locations: {str(e)}"
        )


@router.get("/{location_id}", response_model=LocationWithReviews)
async def get_location(
    location_id: int,
    include_reviews: bool = Query(False, description="Include reviews in response"),
    db: Session = Depends(get_db)
):
    """
    Get a specific location by ID.
    
    Args:
        location_id: The location ID
        include_reviews: Whether to include reviews in the response
        db: Database session
        
    Returns:
        LocationWithReviews: Location information with optional reviews
    """
    location = db.query(Location).filter(Location.id == location_id).first()
    
    if not location:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id {location_id} not found"
        )
    
    if include_reviews:
        reviews = db.query(Review).filter(Review.location_id == location_id).all()
        return LocationWithReviews(
            id=location.id,
            account_id=location.account_id,
            location_id=location.location_id,
            name=location.name,
            address=location.address,
            created_at=location.created_at,
            reviews=reviews
        )
    
    return LocationWithReviews(
        id=location.id,
        account_id=location.account_id,
        location_id=location.location_id,
        name=location.name,
        address=location.address,
        created_at=location.created_at,
        reviews=[]
    )


@router.post("/{account_id}/sync", response_model=List[LocationResponse])
async def sync_locations(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Force synchronization of locations from Google Business Profile for an account.
    
    Args:
        account_id: The account ID to sync locations for
        db: Database session
        
    Returns:
        List[LocationResponse]: List of synchronized locations
    """
    try:
        # Verify account exists
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(
                status_code=404,
                detail=f"Account with id {account_id} not found"
            )
        
        # Sync locations
        business_service = get_google_business_service()
        synced_locations = business_service.sync_locations(account_id, db)
        
        return synced_locations
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error syncing locations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync locations: {str(e)}"
        )


@router.get("/{location_id}/reviews", response_model=List[ReviewResponse])
async def list_reviews(
    location_id: int,
    db: Session = Depends(get_db)
):
    """
    List all reviews for a specific location from the database.
    
    Args:
        location_id: The location ID
        db: Database session
        
    Returns:
        List[ReviewResponse]: List of reviews for the location
    """
    try:
        # Verify location exists
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(
                status_code=404,
                detail=f"Location with id {location_id} not found"
            )
        
        reviews = db.query(Review).filter(Review.location_id == location_id).all()
        return reviews
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing reviews: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list reviews: {str(e)}"
        )


@router.post("/{location_id}/reviews/sync", response_model=List[ReviewResponse])
async def sync_reviews(
    location_id: int,
    db: Session = Depends(get_db)
):
    """
    Synchronize reviews from Google Business Profile API for a location.
    
    Args:
        location_id: The location ID to sync reviews for
        db: Database session
        
    Returns:
        List[ReviewResponse]: List of synchronized reviews
    """
    try:
        # Verify location exists
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(
                status_code=404,
                detail=f"Location with id {location_id} not found"
            )
        
        # Sync reviews
        business_service = get_google_business_service()
        synced_reviews = business_service.sync_reviews(location_id, db)
        
        return synced_reviews
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error syncing reviews: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync reviews: {str(e)}"
        )
