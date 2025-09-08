from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
import models, schemas, auth
from models import household_members
import secrets
import string
from datetime import datetime, timedelta
from email_service import generate_verification_token, send_verification_email, send_password_reset_email, send_household_invitation

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

async def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    verification_token = generate_verification_token()
    
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        verification_token=verification_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    from email_service import send_verification_email
    send_verification_email(user.email, verification_token)
    
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not auth.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def generate_invite_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def create_household(db: Session, household: schemas.HouseholdCreate, owner_id: int):
    invite_code = generate_invite_code()
    db_household = models.Household(
        name=household.name,
        description=household.description,
        invite_code=invite_code,
        owner_id=owner_id
    )
    db.add(db_household)
    db.commit()
    db.refresh(db_household)
    
    # Add owner as member
    owner = get_user_by_id(db, owner_id)
    db_household.members.append(owner)
    db.commit()
    
    # Create default locations
    default_locations = [
        {"name": "Freezer", "location_type": "freezer", "temperature_range": "frozen", "icon": "❄️", "color": "#87CEEB"},
        {"name": "Fridge", "location_type": "fridge", "temperature_range": "cold", "icon": "🥛", "color": "#FFE4E1"},
        {"name": "Pantry", "location_type": "pantry", "temperature_range": "room_temp", "icon": "🏠", "color": "#F5DEB3"}
    ]
    
    for loc_data in default_locations:
        db_location = models.Location(
            name=loc_data["name"],
            location_type=loc_data["location_type"],
            temperature_range=loc_data["temperature_range"],
            icon=loc_data["icon"],
            color=loc_data["color"],
            household_id=db_household.id
        )
        db.add(db_location)
    
    db.commit()
    db.refresh(db_household)
    return db_household

def get_user_households(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    return user.household_memberships if user else []

def get_household_by_id(db: Session, household_id: int):
    return db.query(models.Household).filter(models.Household.id == household_id).first()

def is_household_member(db: Session, household_id: int, user_id: int):
    household = get_household_by_id(db, household_id)
    if not household:
        return False
    user = get_user_by_id(db, user_id)
    return user in household.members

def create_location(db: Session, location: schemas.LocationCreate, household_id: int):
    db_location = models.Location(
        **location.dict(),
        household_id=household_id
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_household_locations(db: Session, household_id: int):
    return db.query(models.Location).filter(models.Location.household_id == household_id).all()

def get_location_by_id(db: Session, location_id: int):
    return db.query(models.Location).filter(models.Location.id == location_id).first()

def create_item(db: Session, item: schemas.ItemCreate, location_id: int, user_id: int = None):
    db_item = models.Item(
        **item.dict(),
        location_id=location_id,
        added_by_user_id=user_id or 1  # Fallback for now
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_location_items(db: Session, location_id: int):
    return db.query(models.Item).options(
        joinedload(models.Item.added_by)
    ).filter(models.Item.location_id == location_id).all()

def verify_email(db: Session, token: str):
    user = db.query(models.User).filter(models.User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    db.refresh(user)
    return user

async def request_password_reset(db: Session, email: str):
    user = get_user_by_email(db, email)
    if not user:
        # Don't reveal that email doesn't exist
        return {"message": "If the email exists, a reset link has been sent"}
    
    reset_token = generate_verification_token()
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Send password reset email
    from email_service import send_password_reset_email
    send_password_reset_email(user.email, reset_token, user.full_name or "User")
    
    return {"message": "Password reset email sent"}

def reset_password(db: Session, token: str, new_password: str):
    user = db.query(models.User).filter(
        models.User.password_reset_token == token,
        models.User.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user.hashed_password = auth.get_password_hash(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    db.refresh(user)
    
    return {"message": "Password reset successfully"}

async def invite_to_household(db: Session, household_id: int, email: str, inviter_id: int):
    household = get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    
    # Check if inviter is household owner or member
    if household.owner_id != inviter_id and not is_household_member(db, household_id, inviter_id):
        raise HTTPException(status_code=403, detail="Only household members can invite others")
    
    # Check if user already exists and is already in household
    invitee = get_user_by_email(db, email)
    if invitee and is_household_member(db, household_id, invitee.id):
        raise HTTPException(status_code=400, detail="User is already a member of this household")
    
    inviter = get_user_by_id(db, inviter_id)
    inviter_name = inviter.full_name or inviter.email
    
    # Send invitation email
    await send_household_invitation(email, household.name, household.invite_code, inviter_name)
    
    return {"message": f"Invitation sent to {email}"}

def join_household(db: Session, invite_code: str, user_id: int):
    household = db.query(models.Household).filter(models.Household.invite_code == invite_code).first()
    if not household:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    user = get_user_by_id(db, user_id)
    if is_household_member(db, household.id, user_id):
        raise HTTPException(status_code=400, detail="You are already a member of this household")
    
    household.members.append(user)
    db.commit()
    db.refresh(household)
    
    return household

def leave_household(db: Session, household_id: int, user_id: int):
    household = get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    
    if household.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Household owner cannot leave household. Transfer ownership first or delete household.")
    
    user = get_user_by_id(db, user_id)
    if not is_household_member(db, household_id, user_id):
        raise HTTPException(status_code=400, detail="You are not a member of this household")
    
    household.members.remove(user)
    db.commit()
    
    return {"message": f"Successfully left {household.name}"}

def update_location(db: Session, location_id: int, location_update: schemas.LocationCreate):
    db_location = get_location_by_id(db, location_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    for key, value in location_update.dict(exclude_unset=True).items():
        setattr(db_location, key, value)
    
    db.commit()
    db.refresh(db_location)
    return db_location

def delete_location(db: Session, location_id: int):
    db_location = get_location_by_id(db, location_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if location has items
    items = get_location_items(db, location_id)
    if items:
        raise HTTPException(status_code=400, detail="Cannot delete location with items. Move items first.")
    
    db.delete(db_location)
    db.commit()
    return {"message": "Location deleted successfully"}

# Additional CRUD functions for item management
def get_user_items(db: Session, user_id: int):
    """Get all items from user's households - optimized with joins"""
    # Single optimized query using joins to eliminate N+1 query problem
    items = db.query(models.Item)\
        .join(models.Location)\
        .join(models.Household)\
        .join(household_members, models.Household.id == household_members.c.household_id)\
        .options(
            joinedload(models.Item.location).joinedload(models.Location.household),
            joinedload(models.Item.added_by)
        )\
        .filter(household_members.c.user_id == user_id)\
        .all()
    
    # Add household_id to each item for convenience (backward compatibility)
    for item in items:
        item.household_id = item.location.household.id
        
    return items

def get_user_locations(db: Session, user_id: int):
    """Get all locations from user's households - optimized with joins"""
    # Single optimized query using joins to eliminate N+1 query problem
    locations = db.query(models.Location)\
        .join(models.Household)\
        .join(household_members, models.Household.id == household_members.c.household_id)\
        .options(joinedload(models.Location.household))\
        .filter(household_members.c.user_id == user_id)\
        .all()
        
    return locations

def get_location_by_name(db: Session, household_id: int, location_name: str):
    """Find location by name within a household"""
    return db.query(models.Location).filter(
        models.Location.household_id == household_id,
        models.Location.name.ilike(f"%{location_name}%")
    ).first()

def get_item_by_id(db: Session, item_id: int):
    """Get item by ID"""
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def update_item(db: Session, item_id: int, item_update: schemas.ItemUpdate):
    """Update an item"""
    db_item = get_item_by_id(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in item_update.dict(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int):
    """Delete an item"""
    db_item = get_item_by_id(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}

# Discord OAuth CRUD functions
def get_user_by_discord_id(db: Session, discord_id: str):
    """Get user by Discord ID"""
    return db.query(models.User).filter(models.User.discord_id == discord_id).first()

async def create_discord_user(db: Session, user_data: schemas.DiscordUserCreate):
    """Create a new user from Discord OAuth"""
    db_user = models.User(
        email=user_data.email,
        full_name=user_data.full_name,
        discord_id=user_data.discord_id,
        discord_username=user_data.discord_username,
        discord_avatar=user_data.discord_avatar,
        auth_provider='discord',
        is_verified=True  # Discord accounts are pre-verified
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default household for Discord user
    household_name = f"{user_data.full_name or user_data.discord_username}'s Household"
    household = create_household(db, schemas.HouseholdCreate(
        name=household_name,
        description="Shared household inventory"
    ), db_user.id)
    
    return db_user

def link_discord_account(db: Session, user: models.User, discord_data: dict):
    """Link Discord account to existing user"""
    user.discord_id = discord_data["id"]
    user.discord_username = discord_data["username"]
    user.discord_avatar = discord_data.get("avatar")
    
    db.commit()
    db.refresh(user)
    return user

def create_login_response(user: models.User):
    """Create login response with JWT token"""
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }