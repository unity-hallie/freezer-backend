"""
User profile routes
"""
from fastapi import APIRouter, Depends

import schemas, models
from auth import get_current_user

# Create router for user endpoints
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user