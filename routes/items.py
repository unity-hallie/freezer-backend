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

# Canonical location helpers to prevent phantom names
CANONICAL = {
    "freezer": ("freezer", "Freezer"),
    "fridge": ("fridge", "Fridge"),
    "pantry": ("pantry", "Pantry"),
}
ALIASES = {
    "refrigerator": "fridge",
}

def normalize_location_name(name: str) -> tuple[str, str]:
    n = (name or "").strip().lower()
    n = ALIASES.get(n, n)
    if n in CANONICAL:
        norm, pretty = CANONICAL[n]
        return norm, pretty
    return n, (name or "").strip().title()

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
    """Create item by specifying location name instead of location_id.
    Normalizes names: 'refrigerator' -> 'Fridge'; only allows canonical locations.
    """
    # Get user's households
    households = crud.get_user_households(db, current_user.id)
    if not households:
        raise HTTPException(status_code=404, detail="No households found")
    
    # Use first household (for simplicity)
    household = households[0]

    norm, pretty = normalize_location_name(location_name)
    allowed = set(CANONICAL.keys())
    if norm not in allowed:
        raise HTTPException(status_code=400, detail="Invalid location_name. Use one of: freezer, fridge, pantry")

    # Prefer exact match by name or location_type
    locations = crud.get_user_locations(db, household.id)
    match = None
    for loc in locations:
        if (loc.name or "").strip().lower() == pretty.lower() or (loc.location_type or "").strip().lower() == norm:
            match = loc
            break

    if not match:
        location_data = schemas.LocationCreate(
            name=pretty,
            location_type=norm,
        )
        match = crud.create_location(db, location_data, household.id)

    return crud.create_item(db=db, item=item, location_id=match.id, user_id=current_user.id)

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
