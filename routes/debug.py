"""
Debug/status endpoints (no secrets). Auth-protected where appropriate.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, crud
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/auth")
def debug_auth(current_user: models.User = Depends(get_current_user)):
    """Echo authenticated identity (no secrets)."""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
    }


@router.get("/inventory")
def debug_inventory(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Summarize household/locations/items for the current user (counts + samples)."""
    households = crud.get_user_households(db, current_user.id) or []
    summary = []
    for h in households:
        locs = crud.get_household_locations(db, h.id)
        loc_summ = []
        for loc in locs:
            items = crud.get_location_items(db, loc.id)
            loc_summ.append({
                "id": loc.id,
                "name": loc.name,
                "location_type": loc.location_type,
                "item_count": len(items),
                "item_samples": [{"id": it.id, "name": it.name} for it in items[:5]]
            })
        summary.append({
            "household_id": h.id,
            "household_name": h.name,
            "locations": loc_summ
        })
    return {"households": summary}

