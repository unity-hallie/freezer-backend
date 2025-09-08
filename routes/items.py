"""
Item management routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

import schemas, crud, models
from auth import get_current_user
from database import get_db
from middleware.auth import verify_item_access, verify_location_access

# Create router for item endpoints
router = APIRouter(tags=["items"])

# Item creation under locations
@router.post("/locations/{location_id}/items", response_model=schemas.ItemResponse)
def create_item(
    location_id: int,
    item: schemas.ItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_location_access(location_id, current_user, db)
    return crud.create_item(db=db, item=item, location_id=location_id, user_id=current_user.id)

# Get all items in a location
@router.get("/locations/{location_id}/items", response_model=list[schemas.ItemResponse])
def get_location_items(
    location_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_location_access(location_id, current_user, db)
    return crud.get_location_items(db, location_id)

# Get all user's items across households
@router.get("/items", response_model=list[schemas.ItemResponse])
def get_user_items(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all items from user's households"""
    return crud.get_user_items(db, current_user.id)

# Create item by location name (convenience endpoint)
@router.post("/items", response_model=schemas.ItemResponse)
def create_item_by_location_name(
    item: schemas.ItemCreate,
    location_name: str = "refrigerator",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create item by specifying location name instead of location_id"""
    # Get user's households
    households = crud.get_user_households(db, current_user.id)
    if not households:
        raise HTTPException(status_code=404, detail="No households found")
    
    # Use first household (for simplicity)
    household = households[0]
    
    # Find or create location by name
    location = crud.get_location_by_name(db, household.id, location_name)
    if not location:
        # Create default location if it doesn't exist
        location_data = schemas.LocationCreate(
            name=location_name.title(),
            location_type=location_name.lower()
        )
        location = crud.create_location(db, location_data, household.id)
    
    return crud.create_item(db=db, item=item, location_id=location.id, user_id=current_user.id)

# Individual item operations
@router.get("/items/{item_id}", response_model=schemas.ItemResponse)
def get_item(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item, _ = verify_item_access(item_id, current_user, db)
    return item

@router.put("/items/{item_id}", response_model=schemas.ItemResponse)
def update_item(
    item_id: int,
    item_update: schemas.ItemUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_item_access(item_id, current_user, db)
    return crud.update_item(db, item_id, item_update)

@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_item_access(item_id, current_user, db)
    crud.delete_item(db, item_id)
    return {"message": "Item deleted successfully"}