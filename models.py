from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

household_members = Table(
    'household_members',
    Base.metadata,
    Column('household_id', Integer, ForeignKey('households.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owned_households = relationship("Household", back_populates="owner")
    household_memberships = relationship("Household", secondary=household_members, back_populates="members")

class Household(Base):
    __tablename__ = "households"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    invite_code = Column(String(10), unique=True, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="owned_households")
    members = relationship("User", secondary=household_members, back_populates="household_memberships")
    locations = relationship("Location", back_populates="household")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location_type = Column(String(50), nullable=False)  # freezer, fridge, pantry, custom
    temperature_range = Column(String(50), nullable=True)  # frozen, cold, room_temp
    icon = Column(String(100), nullable=True)
    color = Column(String(7), nullable=True)  # hex color code
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    household = relationship("Household", back_populates="locations")
    items = relationship("Item", back_populates="location")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=1)
    unit = Column(String(50), nullable=True)  # pieces, lbs, oz, etc.
    expiration_date = Column(DateTime, nullable=True)
    purchase_date = Column(DateTime, nullable=True)
    category = Column(String(100), nullable=True)  # meat, vegetables, dairy, etc.
    barcode = Column(String(50), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    added_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    location = relationship("Location", back_populates="items")
    added_by = relationship("User")