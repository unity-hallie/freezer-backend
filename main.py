from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas, crud, database
from auth import verify_token, get_current_user
from database import get_db
from discord_oauth import DiscordOAuth
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import hashlib
import time

app = FastAPI(title="Freezer App API", version="1.0.0")

# Rate limiting setup - protect against API cost spirals
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Simple in-memory cache for AI requests (prevents duplicate API calls)
ai_cache = {}
CACHE_TTL = 300  # 5 minutes cache

security = HTTPBearer()

# CORS Configuration - Environment-based for production deployment
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

@app.get("/auth/discord/login")
def discord_login():
    """Get Discord OAuth authorization URL"""
    try:
        auth_url = DiscordOAuth.get_authorization_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/discord/callback")
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

# Additional item management endpoints
@app.get("/items", response_model=list[schemas.ItemResponse])
def get_user_items(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all items from user's households"""
    return crud.get_user_items(db, current_user.id)

@app.post("/items", response_model=schemas.ItemResponse)
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

@app.get("/items/{item_id}", response_model=schemas.ItemResponse)
def get_item(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if user has access to this item's household
    location = crud.get_location_by_id(db, item.location_id)
    if not location or not crud.is_household_member(db, location.household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item

@app.put("/items/{item_id}", response_model=schemas.ItemResponse)
def update_item(
    item_id: int,
    item_update: schemas.ItemUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if user has access to this item's household
    location = crud.get_location_by_id(db, item.location_id)
    if not location or not crud.is_household_member(db, location.household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Item not found")
    
    return crud.update_item(db, item_id, item_update)

@app.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if user has access to this item's household
    location = crud.get_location_by_id(db, item.location_id)
    if not location or not crud.is_household_member(db, location.household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Item not found")
    
    crud.delete_item(db, item_id)
    return {"message": "Item deleted successfully"}

@app.get("/locations", response_model=list[schemas.LocationResponse])  
def get_user_locations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all locations from user's households"""
    return crud.get_user_locations(db, current_user.id)

# AI Shopping List Ingestion
@app.post("/api/ingest-shopping")
@limiter.limit("5/minute")  # Strict rate limit - max 5 AI requests per minute per IP
async def ingest_shopping_list(
    request: schemas.ShoppingIngestionRequest,
    request_obj: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parse shopping list/email content using AI and create pending items
    COST SPIRAL PROTECTION: Rate limited, cached, and size validated
    """
    from ai_shopping_parser import shopping_parser
    
    # PROTECTION 1: Input size validation (prevent massive API calls)
    if len(request.content) > 5000:  # Reasonable limit for shopping lists
        raise HTTPException(
            status_code=400, 
            detail="Content too large (max 5000 characters). Please break into smaller chunks."
        )
    
    if len(request.content.strip()) < 10:  # Prevent spam of tiny requests
        raise HTTPException(
            status_code=400, 
            detail="Content too short (min 10 characters). Please provide actual shopping list content."
        )
    
    # PROTECTION 2: Content caching (prevent duplicate API calls)
    content_hash = hashlib.md5(f"{request.content}{request.source_type}".encode()).hexdigest()
    cache_key = f"ai_parse_{content_hash}"
    current_time = time.time()
    
    # Check cache first
    if cache_key in ai_cache:
        cached_result, cached_time = ai_cache[cache_key]
        if current_time - cached_time < CACHE_TTL:
            # Use cached result, no API call needed
            parsed_items = cached_result
        else:
            # Cache expired, remove entry
            del ai_cache[cache_key]
            parsed_items = None
    else:
        parsed_items = None
    
    try:
        # Only make API call if not cached
        if parsed_items is None:
            # Parse content with AI
            parsed_items = shopping_parser.parse_shopping_content(
                content=request.content,
                source_type=request.source_type or "generic"
            )
            
            # Cache the result
            ai_cache[cache_key] = (parsed_items, current_time)
            
            # PROTECTION 3: Cache cleanup (prevent memory growth)
            if len(ai_cache) > 100:  # Keep cache size reasonable
                # Remove oldest entries
                oldest_keys = sorted(ai_cache.keys(), key=lambda k: ai_cache[k][1])[:20]
                for old_key in oldest_keys:
                    del ai_cache[old_key]
        
        # Validate parsed items
        validated_items = shopping_parser.validate_items(parsed_items)
        
        if not validated_items:
            raise HTTPException(status_code=400, detail="No valid grocery items found in content")
        
        # Get user's household
        households = crud.get_user_households(db, current_user.id)
        if not households:
            raise HTTPException(status_code=404, detail="No households found")
        
        household = households[0]  # Use first household
        
        # Create items with ai-generated tag
        created_items = []
        parsing_log = []
        
        for parsed_item in validated_items:
            try:
                # Find or create appropriate location
                location_name = {
                    "freezer": "freezer", 
                    "fridge": "refrigerator",
                    "pantry": "pantry"
                }.get(parsed_item.category, "pantry")
                
                location = crud.get_location_by_name(db, household.id, location_name)
                if not location:
                    # Create location if it doesn't exist
                    location_data = schemas.LocationCreate(
                        name=location_name.title(),
                        location_type=location_name,
                        household_id=household.id
                    )
                    location = crud.create_location(db, location_data)
                
                # Create item with AI-generated tags
                tags = ["ai-generated", f"confidence-{int(parsed_item.confidence * 100)}"]
                if request.source_type:
                    tags.append(f"source-{request.source_type}")
                
                item_data = schemas.ItemCreate(
                    name=parsed_item.name,
                    quantity=parsed_item.quantity,
                    unit=parsed_item.unit,
                    tags=tags,
                    description=f"Auto-imported from {request.source_type or 'shopping list'}"
                )
                
                item = crud.create_item(
                    db=db, 
                    item=item_data, 
                    location_id=location.id, 
                    user_id=current_user.id
                )
                created_items.append(item)
                
                # Log parsing details
                parsing_log.append({
                    "item_id": item.id,
                    "parsed_name": parsed_item.name,
                    "confidence": parsed_item.confidence,
                    "category": parsed_item.category,
                    "raw_text": parsed_item.raw_text
                })
                
            except Exception as e:
                # Continue with other items if one fails
                parsing_log.append({
                    "error": str(e),
                    "parsed_name": parsed_item.name,
                    "skipped": True
                })
                continue
        
        return {
            "message": f"Successfully imported {len(created_items)} items from {request.source_type or 'shopping list'}",
            "items_created": len(created_items),
            "total_parsed": len(validated_items),
            "items": [schemas.ItemResponse.from_orm(item) for item in created_items],
            "parsing_log": parsing_log,
            "requires_review": True,
            "review_instructions": "Items tagged 'ai-generated' should be reviewed and confirmed or modified"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shopping list parsing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)