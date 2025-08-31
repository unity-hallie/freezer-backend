from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class DiscordUserCreate(UserBase):
    discord_id: str
    discord_username: Optional[str] = None
    discord_avatar: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_verified: bool
    created_at: datetime
    discord_id: Optional[str] = None
    discord_username: Optional[str] = None
    discord_avatar: Optional[str] = None
    auth_provider: Optional[str] = "email"

class UserProfile(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    discord_id: Optional[str] = None
    discord_username: Optional[str] = None
    discord_avatar: Optional[str] = None
    auth_provider: Optional[str] = "email"
    
    class Config:
        from_attributes = True

class HouseholdBase(BaseModel):
    name: str
    description: Optional[str] = None

class HouseholdCreate(HouseholdBase):
    pass

class HouseholdResponse(HouseholdBase):
    id: int
    owner_id: int
    invite_code: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class LocationBase(BaseModel):
    name: str
    location_type: str
    temperature_range: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int
    household_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: int = 1
    unit: Optional[str] = None
    expiration_date: Optional[datetime] = None
    purchase_date: Optional[datetime] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    tags: Optional[List[str]] = []
    custom_expiration_days: Optional[int] = None
    emoji: Optional[str] = None
    date_added: Optional[datetime] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    expiration_date: Optional[datetime] = None
    purchase_date: Optional[datetime] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_expiration_days: Optional[int] = None
    emoji: Optional[str] = None
    date_added: Optional[datetime] = None

class ItemResponse(ItemBase):
    id: int
    location_id: int
    added_by_user_id: int
    created_at: datetime
    updated_at: datetime
    added_by: Optional[UserProfile] = None  # Include user profile
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class EmailVerification(BaseModel):
    token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class HouseholdInvite(BaseModel):
    email: EmailStr

class JoinHousehold(BaseModel):
    invite_code: str

# AI Shopping List Ingestion
class ShoppingIngestionRequest(BaseModel):
    content: str  # Email content or shopping list text
    source_type: Optional[str] = "generic"  # hannaford, instacart, amazon_fresh, generic
    
class ShoppingIngestionResponse(BaseModel):
    message: str
    items_created: int
    total_parsed: int
    items: List['ItemResponse']
    parsing_log: List[dict]
    requires_review: bool
    review_instructions: str