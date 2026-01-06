"""Google Business Profile API service."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from app.models.database import Account, Location, Review
from app.services.google_auth import get_google_auth_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class GoogleBusinessService:
    """Service for interacting with Google Business Profile API."""
    
    def __init__(self):
        """Initialize the Google Business service."""
        self.auth_service = get_google_auth_service()
    
    def _get_credentials(self, account: Account, db: Session) -> Credentials:
        """
        Get valid credentials for an account, refreshing if necessary.
        
        Args:
            account: The account model
            db: Database session for committing token updates
            
        Returns:
            Credentials: Valid Google OAuth credentials
        """
        # Check if token needs refresh
        if self.auth_service.is_token_expired(account.token_expiry) and account.refresh_token:
            try:
                token_data = self.auth_service.refresh_access_token(account.refresh_token)
                account.access_token = token_data["access_token"]
                account.token_expiry = token_data["token_expiry"]
                account.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Token refreshed for account {account.id}")
                return Credentials(
                    token=account.access_token,
                    refresh_token=account.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.GOOGLE_CLIENT_ID,
                    client_secret=settings.GOOGLE_CLIENT_SECRET
                )
            except Exception as e:
                logger.error(f"Failed to refresh token for account {account.id}: {e}")
                raise ValueError(f"Failed to refresh access token: {str(e)}")
        
        return Credentials(
            token=account.access_token,
            refresh_token=account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
    
    def _get_account_id(self, credentials: Credentials) -> str:
        """
        Get the Google account ID (account name) for the authenticated user.
        
        Args:
            credentials: Google OAuth credentials
            
        Returns:
            str: The account ID (e.g., "accounts/123456789")
        """
        try:
            service = build('mybusinessaccountmanagement', 'v1', credentials=credentials)
            accounts = service.accounts().list().execute()
            
            if not accounts or 'accounts' not in accounts or len(accounts['accounts']) == 0:
                raise ValueError("No Google Business Profile accounts found")
            
            # Return the first account's name (format: accounts/123456789)
            return accounts['accounts'][0]['name']
        except HttpError as e:
            logger.error(f"Failed to get account ID: {e}")
            raise ValueError(f"Failed to retrieve account ID: {str(e)}")
    
    def get_locations(self, account_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        Retrieve all locations for a Google Business Profile account.
        
        Args:
            account_id: The database account ID
            db: Database session
            
        Returns:
            List[Dict]: List of location dictionaries
        """
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account with id {account_id} not found")
        
        try:
            credentials = self._get_credentials(account, db)
            google_account_id = self._get_account_id(credentials)
            
            # Build the Business Information API service
            service = build('mybusinessbusinessinformation', 'v1', credentials=credentials)
            
            locations = []
            page_token = None
            
            while True:
                # Request locations
                request = service.accounts().locations().list(
                    parent=google_account_id,
                    pageSize=100
                )
                
                if page_token:
                    request.pageToken = page_token
                
                response = request.execute()
                
                if 'locations' in response:
                    locations.extend(response['locations'])
                
                # Check for next page
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            return locations
            
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            logger.error(f"Google API error while fetching locations: {error_details}")
            raise ValueError(f"Failed to fetch locations from Google API: {error_details}")
        except Exception as e:
            logger.error(f"Unexpected error while fetching locations: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")
    
    def sync_locations(self, account_id: int, db: Session) -> List[Location]:
        """
        Synchronize locations from Google API and save them to database.
        
        Args:
            account_id: The database account ID
            db: Database session
            
        Returns:
            List[Location]: List of synchronized Location models
        """
        google_locations = self.get_locations(account_id, db)
        account = db.query(Account).filter(Account.id == account_id).first()
        
        synced_locations = []
        
        for google_location in google_locations:
            location_id = google_location.get('name', '').split('/')[-1]  # Extract ID from name
            location_name = google_location.get('title', 'Unknown Location')
            location_address = google_location.get('storefrontAddress', {})
            address_str = None
            
            if location_address:
                address_parts = []
                if 'addressLines' in location_address:
                    address_parts.extend(location_address['addressLines'])
                if 'locality' in location_address:
                    address_parts.append(location_address['locality'])
                if 'postalCode' in location_address:
                    address_parts.append(location_address['postalCode'])
                if 'regionCode' in location_address:
                    address_parts.append(location_address['regionCode'])
                address_str = ', '.join(address_parts) if address_parts else None
            
            # Check if location already exists
            existing_location = db.query(Location).filter(
                Location.location_id == location_id
            ).first()
            
            if existing_location:
                # Update existing location
                existing_location.name = location_name
                existing_location.address = address_str
                synced_locations.append(existing_location)
            else:
                # Create new location
                new_location = Location(
                    account_id=account_id,
                    location_id=location_id,
                    name=location_name,
                    address=address_str
                )
                db.add(new_location)
                synced_locations.append(new_location)
        
        db.commit()
        
        # Refresh all locations to get IDs
        for location in synced_locations:
            db.refresh(location)
        
        return synced_locations
    
    def get_reviews(
        self,
        location_id: int,
        db: Session,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve reviews for a specific location.
        
        Args:
            location_id: The database location ID
            db: Database session
            page_token: Optional pagination token
            
        Returns:
            Dict: Dictionary containing reviews and next page token
        """
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise ValueError(f"Location with id {location_id} not found")
        
        account = db.query(Account).filter(Account.id == location.account_id).first()
        if not account:
            raise ValueError(f"Account for location {location_id} not found")
        
        try:
            credentials = self._get_credentials(account, db)
            google_account_id = self._get_account_id(credentials)
            
            # Build the My Business API service (v4 for reviews)
            service = build('mybusiness', 'v4', credentials=credentials)
            
            # Format: accounts/{accountId}/locations/{locationId}
            location_path = f"{google_account_id}/locations/{location.location_id}"
            
            # Request reviews
            request = service.accounts().locations().reviews().list(
                parent=location_path,
                pageSize=50
            )
            
            if page_token:
                request.pageToken = page_token
            
            response = request.execute()
            
            reviews = response.get('reviews', [])
            next_page_token = response.get('nextPageToken')
            
            return {
                'reviews': reviews,
                'nextPageToken': next_page_token
            }
            
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            logger.error(f"Google API error while fetching reviews: {error_details}")
            raise ValueError(f"Failed to fetch reviews from Google API: {error_details}")
        except Exception as e:
            logger.error(f"Unexpected error while fetching reviews: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")
    
    def sync_reviews(self, location_id: int, db: Session) -> List[Review]:
        """
        Synchronize reviews from Google API and save them to database.
        
        Args:
            location_id: The database location ID
            db: Database session
            
        Returns:
            List[Review]: List of synchronized Review models
        """
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise ValueError(f"Location with id {location_id} not found")
        
        synced_reviews = []
        page_token = None
        
        while True:
            # Fetch reviews page by page
            reviews_data = self.get_reviews(location_id, db, page_token)
            google_reviews = reviews_data.get('reviews', [])
            
            for google_review in google_reviews:
                review_id = google_review.get('reviewId', '')
                author_name = google_review.get('reviewer', {}).get('displayName', 'Anonymous')
                rating = google_review.get('starRating', {}).get('rating', 0)
                comment = google_review.get('comment', '')
                
                # Parse reply if exists
                reply = None
                reply_time = None
                if 'reviewReply' in google_review:
                    reply = google_review['reviewReply'].get('comment', '')
                    reply_time_str = google_review['reviewReply'].get('updateTime')
                    if reply_time_str:
                        try:
                            reply_time = datetime.fromisoformat(reply_time_str.replace('Z', '+00:00'))
                        except:
                            pass
                
                # Parse creation time
                create_time_str = google_review.get('createTime', '')
                created_at = datetime.utcnow()
                if create_time_str:
                    try:
                        created_at = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                # Check if review already exists
                existing_review = db.query(Review).filter(
                    Review.review_id == review_id
                ).first()
                
                if existing_review:
                    # Update existing review
                    existing_review.author_name = author_name
                    existing_review.rating = rating
                    existing_review.comment = comment
                    existing_review.reply = reply
                    existing_review.reply_time = reply_time
                    existing_review.synced_at = datetime.utcnow()
                    synced_reviews.append(existing_review)
                else:
                    # Create new review
                    new_review = Review(
                        location_id=location_id,
                        review_id=review_id,
                        author_name=author_name,
                        rating=rating,
                        comment=comment,
                        reply=reply,
                        reply_time=reply_time,
                        created_at=created_at
                    )
                    db.add(new_review)
                    synced_reviews.append(new_review)
            
            # Check for next page
            page_token = reviews_data.get('nextPageToken')
            if not page_token:
                break
        
        db.commit()
        
        # Refresh all reviews to get IDs
        for review in synced_reviews:
            db.refresh(review)
        
        return synced_reviews
    
    def reply_to_review(
        self,
        location_id: int,
        review_id: str,
        reply_text: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Send a reply to a review via Google Business Profile API.
        
        Args:
            location_id: The database location ID
            review_id: The Google review ID
            reply_text: The reply text to send
            db: Database session
            
        Returns:
            Dict: Response from Google API
        """
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise ValueError(f"Location with id {location_id} not found")
        
        account = db.query(Account).filter(Account.id == location.account_id).first()
        if not account:
            raise ValueError(f"Account for location {location_id} not found")
        
        try:
            credentials = self._get_credentials(account, db)
            google_account_id = self._get_account_id(credentials)
            
            # Build the My Business API service (v4 for replies)
            service = build('mybusiness', 'v4', credentials=credentials)
            
            # Format: accounts/{accountId}/locations/{locationId}/reviews/{reviewId}
            review_path = f"{google_account_id}/locations/{location.location_id}/reviews/{review_id}"
            
            # Prepare reply body
            reply_body = {
                'reply': {
                    'comment': reply_text
                }
            }
            
            # Send reply (PUT method)
            response = service.accounts().locations().reviews().updateReply(
                name=review_path,
                body=reply_body
            ).execute()
            
            # Update the review in database
            review = db.query(Review).filter(Review.review_id == review_id).first()
            if review:
                review.reply = reply_text
                review.reply_time = datetime.utcnow()
                db.commit()
            
            return response
            
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            logger.error(f"Google API error while sending reply: {error_details}")
            raise ValueError(f"Failed to send reply to Google API: {error_details}")
        except Exception as e:
            logger.error(f"Unexpected error while sending reply: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")
    
    def delete_reply(
        self,
        location_id: int,
        review_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Delete a reply from a review via Google Business Profile API.
        
        Args:
            location_id: The database location ID
            review_id: The Google review ID
            db: Database session
            
        Returns:
            Dict: Response from Google API
        """
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise ValueError(f"Location with id {location_id} not found")
        
        account = db.query(Account).filter(Account.id == location.account_id).first()
        if not account:
            raise ValueError(f"Account for location {location_id} not found")
        
        try:
            credentials = self._get_credentials(account, db)
            google_account_id = self._get_account_id(credentials)
            
            # Build the My Business API service (v4 for replies)
            service = build('mybusiness', 'v4', credentials=credentials)
            
            # Format: accounts/{accountId}/locations/{locationId}/reviews/{reviewId}
            review_path = f"{google_account_id}/locations/{location.location_id}/reviews/{review_id}"
            
            # Delete reply
            response = service.accounts().locations().reviews().deleteReply(
                name=review_path
            ).execute()
            
            # Update the review in database
            review = db.query(Review).filter(Review.review_id == review_id).first()
            if review:
                review.reply = None
                review.reply_time = None
                db.commit()
            
            return response
            
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            logger.error(f"Google API error while deleting reply: {error_details}")
            raise ValueError(f"Failed to delete reply from Google API: {error_details}")
        except Exception as e:
            logger.error(f"Unexpected error while deleting reply: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")


# Singleton instance
_google_business_service = None

def get_google_business_service() -> GoogleBusinessService:
    """Get or create the Google Business service instance."""
    global _google_business_service
    if _google_business_service is None:
        _google_business_service = GoogleBusinessService()
    return _google_business_service
