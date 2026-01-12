"""Authentication routes for Google OAuth."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db, Account
from app.services.google_auth import get_google_auth_service
from app.config import settings
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])


class AccountResponse(BaseModel):
    """Response model for account information."""
    id: int
    google_email: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/login")
async def login():
    """
    Redirect to Google OAuth authorization page.
    
    Returns:
        RedirectResponse: Redirects to Google OAuth consent screen
    """
    try:
        auth_service = get_google_auth_service()
        authorization_url = auth_service.get_authorization_url()
        return RedirectResponse(url=authorization_url)
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@router.get("/callback")
async def callback(
    code: str = Query(..., description="Authorization code from Google"),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Google.
    
    Args:
        code: Authorization code from Google
        db: Database session
        
    Returns:
        dict: Success message with account information
    """
    try:
        # Exchange code for tokens
        auth_service = get_google_auth_service()
        token_data = auth_service.exchange_code_for_tokens(code)
        
        # Check if account already exists
        existing_account = db.query(Account).filter(
            Account.google_email == token_data["email"]
        ).first()
        
        if existing_account:
            # Update existing account
            existing_account.access_token = token_data["access_token"]
            existing_account.refresh_token = token_data["refresh_token"]
            existing_account.token_expiry = token_data["token_expiry"]
            existing_account.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_account)
            
            return {
                "message": "Account updated successfully",
                "account": {
                    "id": existing_account.id,
                    "email": existing_account.google_email
                }
            }
        else:
            # Create new account
            new_account = Account(
                google_email=token_data["email"],
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expiry=token_data["token_expiry"]
            )
            db.add(new_account)
            db.commit()
            db.refresh(new_account)
            
            return {
                "message": "Account connected successfully",
                "account": {
                    "id": new_account.id,
                    "email": new_account.google_email
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process OAuth callback: {str(e)}"
        )


@router.get("/accounts", response_model=List[AccountResponse])
async def list_accounts(db: Session = Depends(get_db)):
    """
    List all connected Google accounts.
    
    Args:
        db: Database session
        
    Returns:
        List[AccountResponse]: List of all connected accounts
    """
    accounts = db.query(Account).all()
    return accounts


@router.delete("/accounts/{account_id}")
async def disconnect_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Disconnect a Google account by deleting it.
    
    Args:
        account_id: ID of the account to disconnect
        db: Database session
        
    Returns:
        dict: Success message
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=404,
            detail=f"Account with id {account_id} not found"
        )
    
    db.delete(account)
    db.commit()
    
    return {
        "message": f"Account {account.google_email} disconnected successfully"
    }


