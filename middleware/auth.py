"""
Authorization middleware for DRY principle compliance
Eliminates repeated permission checking patterns across endpoints
"""

from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Callable, Any
import crud
import models
from database import get_db
from auth import get_current_user


def verify_location_access(location_id: int, current_user: models.User, db: Session) -> models.Location:
    """
    Utility function to verify user has access to a location through household membership.
    Returns the location if access is granted, raises HTTPException otherwise.
    """
    location = crud.get_location_by_id(db, location_id)
    if not location or not crud.is_household_member(db, location.household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Location not found")
    return location


def verify_item_access(item_id: int, current_user: models.User, db: Session) -> tuple[models.Item, models.Location]:
    """
    Utility function to verify user has access to an item through household membership.
    Returns (item, location) if access is granted, raises HTTPException otherwise.
    """
    item = crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    location = crud.get_location_by_id(db, item.location_id)
    if not location or not crud.is_household_member(db, location.household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item, location


def verify_household_access(household_id: int, current_user: models.User, db: Session) -> models.Household:
    """
    Utility function to verify user is a member of the specified household.
    Returns household if access is granted, raises HTTPException otherwise.
    """
    if not crud.is_household_member(db, household_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    household = crud.get_household_by_id(db, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    
    return household