"""
Authentication routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

import schemas, crud, models
from auth import get_current_user
from database import get_db
from discord_oauth import DiscordOAuth

# Create router for auth endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=schemas.UserResponse)
@limiter.limit("3/minute")  # Prevent registration abuse
async def register(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db=db, user=user)

@router.post("/login")
@limiter.limit("10/minute")  # Prevent brute force attacks
def login(request: Request, user: schemas.UserLogin, db: Session = Depends(get_db)):
    return crud.authenticate_user(db, user.email, user.password)

@router.get("/discord/login")
def discord_login():
    """Get Discord OAuth authorization URL"""
    try:
        auth_url = DiscordOAuth.get_authorization_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/discord/callback")
async def discord_callback(code: str, db: Session = Depends(get_db)):
    """Handle Discord OAuth callback"""
    try:
        # Exchange code for access token
        token_data = await DiscordOAuth.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        
        # Get Discord user info
        discord_user = await DiscordOAuth.get_user_info(access_token)
        
        # Check if user already exists by Discord ID
        existing_user = crud.get_user_by_discord_id(db, discord_user["id"])
        
        if existing_user:
            # User exists, log them in
            return crud.create_login_response(existing_user)
        else:
            # Create new user from Discord data
            email = discord_user.get("email")
            if not email:
                raise HTTPException(status_code=400, detail="Discord account must have a verified email")
            
            # Check if email already exists
            email_user = crud.get_user_by_email(db, email)
            if email_user:
                # Link Discord account to existing email account
                crud.link_discord_account(db, email_user, discord_user)
                return crud.create_login_response(email_user)
            else:
                # Create new user
                user_data = schemas.DiscordUserCreate(
                    email=email,
                    full_name=discord_user.get("username"),
                    discord_id=discord_user["id"],
                    discord_username=discord_user["username"],
                    discord_avatar=discord_user.get("avatar")
                )
                new_user = await crud.create_discord_user(db, user_data)
                return crud.create_login_response(new_user)
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-email")
def verify_email(verification: schemas.EmailVerification, db: Session = Depends(get_db)):
    user = crud.verify_email(db, verification.token)
    return {"message": "Email verified successfully"}

@router.post("/request-password-reset")
@limiter.limit("5/hour")  # Prevent email spam abuse
async def request_password_reset(request_obj: Request, request: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    return await crud.request_password_reset(db, request.email)

@router.post("/reset-password")
def reset_password(reset: schemas.PasswordReset, db: Session = Depends(get_db)):
    return crud.reset_password(db, reset.token, reset.new_password)