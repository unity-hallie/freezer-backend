from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas, crud, database
from auth import verify_token, get_current_user
from database import get_db
import os

app = FastAPI(title="Freezer App API", version="1.0.0")

security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def root():
    return {"message": "Freezer App API"}

@app.post("/auth/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db=db, user=user)

@app.post("/auth/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    return crud.authenticate_user(db, user.email, user.password)

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/auth/verify-email")
def verify_email(verification: schemas.EmailVerification, db: Session = Depends(get_db)):
    user = crud.verify_email(db, verification.token)
    return {"message": "Email verified successfully"}

@app.post("/auth/request-password-reset")
async def request_password_reset(request: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    return await crud.request_password_reset(db, request.email)

@app.post("/auth/reset-password")
def reset_password(reset: schemas.PasswordReset, db: Session = Depends(get_db)):
    return crud.reset_password(db, reset.token, reset.new_password)

@app.post("/households", response_model=schemas.HouseholdResponse)
def create_household(
    household: schemas.HouseholdCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.create_household(db=db, household=household, owner_id=current_user.id)

@app.get("/households", response_model=list[schemas.HouseholdResponse])
def get_user_households(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_user_households(db, user_id=current_user.id)

@app.post("/households/{household_id}/invite")
async def invite_to_household(
    household_id: int,
    invite: schemas.HouseholdInvite,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await crud.invite_to_household(db, household_id, invite.email, current_user.id)

@app.post("/households/join", response_model=schemas.HouseholdResponse)
def join_household(
    join_request: schemas.JoinHousehold,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.join_household(db, join_request.invite_code, current_user.id)

@app.delete("/households/{household_id}/leave")
def leave_household(
    household_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.leave_household(db, household_id, current_user.id)

@app.post("/households/{household_id}/locations", response_model=schemas.LocationResponse)
def create_location(
    household_id: int,
    location: schemas.LocationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    household = crud.get_household_by_id(db, household_id)
    if not household or not crud.is_household_member(db, household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Household not found")
    return crud.create_location(db=db, location=location, household_id=household_id)

@app.get("/households/{household_id}/locations", response_model=list[schemas.LocationResponse])
def get_household_locations(
    household_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not crud.is_household_member(db, household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Household not found")
    return crud.get_household_locations(db, household_id)

@app.put("/locations/{location_id}", response_model=schemas.LocationResponse)
def update_location(
    location_id: int,
    location_update: schemas.LocationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    location = crud.get_location_by_id(db, location_id)
    if not location or not crud.is_household_member(db, location.household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Location not found")
    return crud.update_location(db, location_id, location_update)

@app.delete("/locations/{location_id}")
def delete_location(
    location_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    location = crud.get_location_by_id(db, location_id)
    if not location or not crud.is_household_member(db, location.household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Location not found")
    return crud.delete_location(db, location_id)

@app.post("/locations/{location_id}/items", response_model=schemas.ItemResponse)
def create_item(
    location_id: int,
    item: schemas.ItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    location = crud.get_location_by_id(db, location_id)
    if not location or not crud.is_household_member(db, location.household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Location not found")
    return crud.create_item(db=db, item=item, location_id=location_id, user_id=current_user.id)

@app.get("/locations/{location_id}/items", response_model=list[schemas.ItemResponse])
def get_location_items(
    location_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    location = crud.get_location_by_id(db, location_id)
    if not location or not crud.is_household_member(db, location.household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Location not found")
    return crud.get_location_items(db, location_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)