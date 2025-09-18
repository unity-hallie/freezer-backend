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

# Import route modules
from routes.auth import router as auth_router
from routes.households import router as households_router
from routes.locations import router as locations_router
from routes.items import router as items_router
from routes.users import router as users_router

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

# Include routers
app.include_router(auth_router)
app.include_router(households_router)
app.include_router(locations_router)
app.include_router(items_router)
app.include_router(users_router)

@app.get("/")
def root():
    return {"message": "Freezer App API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Enhanced health check endpoint with database connectivity validation"""
    import datetime
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "service": "freezer-api",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "checks": {
            "database": "unknown",
            "api": "healthy"
        }
    }
    
    # Test database connectivity
    try:
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            health_status["checks"]["database"] = "healthy"
        else:
            health_status["checks"]["database"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Set appropriate HTTP status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    from fastapi import Response
    return Response(
        content=schemas.HealthResponse(**health_status).model_dump_json(),
        status_code=status_code,
        media_type="application/json"
    )

@app.get("/api/health")  
def api_health_check(db: Session = Depends(get_db)):
    """Detailed API health endpoint for deployment monitoring"""
    import datetime
    from sqlalchemy import text
    
    health_data = {
        "service": "freezer-api",
        "status": "operational", 
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "checks": {
            "database_connection": "unknown",
            "database_query": "unknown", 
            "cors_configured": bool(allowed_origins),
            "rate_limiting": bool(limiter)
        }
    }
    
    # Database connectivity test
    try:
        db.execute(text("SELECT 1")).scalar()
        health_data["checks"]["database_connection"] = "healthy"
        
        # Test actual query capability
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        health_data["checks"]["database_query"] = "healthy"
        health_data["stats"] = {
            "total_users": user_count,
            "database_responsive": True
        }
    except Exception as e:
        health_data["checks"]["database_connection"] = f"unhealthy: {str(e)}"
        health_data["checks"]["database_query"] = "failed" 
        health_data["status"] = "degraded"
        health_data["stats"] = {
            "database_responsive": False
        }
    
    status_code = 200 if health_data["status"] == "operational" else 503
    
    from fastapi import Response
    return Response(
        content=schemas.ApiHealthResponse(**health_data).model_dump_json(),
        status_code=status_code,
        media_type="application/json"
    )

@app.get("/api/")
def api_root():
    """API root endpoint"""
    return {"message": "Freezer App API v1.0.0", "status": "operational"}


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