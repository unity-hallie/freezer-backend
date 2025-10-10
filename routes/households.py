"""
Household management routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

import schemas, crud, models
from auth import get_current_user
from database import get_db

# Create router for household endpoints
router = APIRouter(prefix="/households", tags=["households"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@router.post("", response_model=schemas.HouseholdResponse)
def create_household(
    household: schemas.HouseholdCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.create_household(db=db, household=household, owner_id=current_user.id)

@router.get("", response_model=list[schemas.HouseholdResponse])
def get_user_households(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_user_households(db, user_id=current_user.id)

@router.post("/{household_id}/invite")
@limiter.limit("10/hour")  # Prevent invitation spam
async def invite_to_household(
    request: Request,
    household_id: int,
    invite: schemas.HouseholdInvite,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await crud.invite_to_household(db, household_id, invite.email, current_user.id)

@router.post("/join", response_model=schemas.HouseholdResponse)
def join_household(
    join_request: schemas.JoinHousehold,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.join_household(db, join_request.invite_code, current_user.id)

@router.delete("/{household_id}/leave")
def leave_household(
    household_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.leave_household(db, household_id, current_user.id)
@router.patch("/{household_id}", response_model=schemas.HouseholdResponse)
def update_household_discord(
    household_id: int,
    update: schemas.HouseholdDiscordUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify user is owner or member
    household = crud.get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    
    if household.owner_id != current_user.id and current_user not in household.members:
        raise HTTPException(status_code=403, detail="Not authorized to update this household")
    
    # Update Discord fields
    if update.discord_guild_id is not None:
        household.discord_guild_id = update.discord_guild_id
    if update.discord_notification_channel_id is not None:
        household.discord_notification_channel_id = update.discord_notification_channel_id
    
    db.commit()
    db.refresh(household)
    return household
