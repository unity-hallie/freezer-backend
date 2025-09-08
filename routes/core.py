"""
Core API routes (health checks, root, AI services)
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import datetime
import hashlib
import time
from sqlalchemy import text

import schemas, crud, models
from auth import get_current_user
from database import get_db
from config import get_config

# Create router for core endpoints
router = APIRouter(tags=["core"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Simple in-memory cache for AI requests (prevents duplicate API calls)
ai_cache = {}
CACHE_TTL = 300  # 5 minutes cache

@router.get("/")
def root():
    return {"message": "Freezer App API"}

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Enhanced health check endpoint with database connectivity validation"""
    try:
        # Test database connectivity with a simple query
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        status_code = 200
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        status_code = 503
    
    response = {
        "status": "healthy" if status_code == 200 else "unhealthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "service": "freezer-api",
        "version": "1.0.0",
        "database": db_status
    }
    
    return response

@router.get("/api/health")
def api_health_check(db: Session = Depends(get_db)):
    """Comprehensive API health check with detailed system information"""
    try:
        # Test database with actual query
        result = db.execute(text("SELECT COUNT(*) as user_count FROM users")).fetchone()
        user_count = result.user_count if result else 0
        
        # Test database performance
        start_time = time.time()
        db.execute(text("SELECT 1"))
        query_time_ms = round((time.time() - start_time) * 1000, 2)
        
        db_status = "operational"
        overall_status = "operational"
        status_code = 200
    except Exception as e:
        db_status = f"error: {str(e)}"
        overall_status = "degraded"
        user_count = 0
        query_time_ms = 0
        status_code = 503
    
    allowed_origins = get_config("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    
    response = {
        "service": "freezer-api",
        "status": overall_status, 
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "environment": get_config("ENVIRONMENT", "production"),
        "checks": {
            "database_connection": db_status,
            "database_query": f"{query_time_ms}ms", 
            "cors_configured": bool(allowed_origins),
            "rate_limiting": "enabled"
        },
        "stats": {
            "total_users": user_count,
            "uptime": "runtime_dependent",
            "cache_size": len(ai_cache)
        }
    }
    
    return response

@router.get("/api/")
def api_info():
    """API information endpoint"""
    return {"message": "Freezer App API - see /docs for documentation"}

@router.post("/api/ingest-shopping")
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
            parsed_items = await shopping_parser.parse_shopping_content(
                content=request.content,
                source_type=request.source_type,
                household_context=request.household_context
            )
            
            # Cache the result to prevent duplicate API calls
            ai_cache[cache_key] = (parsed_items, current_time)
            
            # PROTECTION 3: Cache cleanup (prevent memory bloat)
            if len(ai_cache) > 1000:  # Reasonable cache size limit
                # Remove oldest entries
                oldest_keys = sorted(ai_cache.keys(), key=lambda k: ai_cache[k][1])[:500]
                for key in oldest_keys:
                    del ai_cache[key]
        
        # Convert parsed items to database items
        created_items = []
        for item_data in parsed_items.get('items', []):
            try:
                # Get or create location
                households = crud.get_user_households(db, current_user.id)
                if not households:
                    raise HTTPException(status_code=404, detail="No households found")
                
                household = households[0]  # Use first household
                location_name = item_data.get('suggested_location', 'refrigerator')
                location = crud.get_location_by_name(db, household.id, location_name)
                
                if not location:
                    # Create location if it doesn't exist
                    location_data = schemas.LocationCreate(
                        name=location_name.title(),
                        location_type=location_name.lower()
                    )
                    location = crud.create_location(db, location_data, household.id)
                
                # Create the item
                item_create = schemas.ItemCreate(
                    name=item_data['name'],
                    quantity=item_data.get('quantity', 1),
                    category=item_data.get('category', 'general'),
                    description=item_data.get('description', ''),
                    expiration_date=item_data.get('expiration_date')
                )
                
                new_item = crud.create_item(db, item_create, location.id, current_user.id)
                created_items.append(new_item)
                
            except Exception as item_error:
                # Log item creation error but continue with others
                print(f"Failed to create item {item_data.get('name', 'unknown')}: {item_error}")
                continue
        
        return {
            "success": True,
            "items_created": len(created_items),
            "total_parsed": len(parsed_items.get('items', [])),
            "items": [schemas.ItemResponse.from_orm(item) for item in created_items],
            "ai_insights": parsed_items.get('insights', {}),
            "cached": cache_key in ai_cache and current_time - ai_cache[cache_key][1] < CACHE_TTL
        }
        
    except Exception as e:
        # Handle AI parsing errors gracefully
        raise HTTPException(
            status_code=500,
            detail=f"AI parsing failed: {str(e)}"
        )