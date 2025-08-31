"""
TDD Test: Household owner should be automatically added as member
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
import crud
import schemas

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_household_owner_becomes_member():
    """FAILING TEST: Owner should be household member after creation"""
    
    # Setup database
    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        # Create a user directly (avoiding async)
        user = models.User(
            email="test@example.com", 
            hashed_password="hashedpassword",  # simplified for test
            full_name="Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create household with this user as owner
        household_data = schemas.HouseholdCreate(name="Test House", description="Test")
        household = crud.create_household(db, household_data, user.id)
        
        # TEST: Owner should be a member of their own household
        is_member = crud.is_household_member(db, household.id, user.id)
        
        print(f"User ID: {user.id}")
        print(f"Household ID: {household.id}")  
        print(f"Household owner_id: {household.owner_id}")
        print(f"Is owner a member? {is_member}")
        print(f"Household members: {[member.id for member in household.members]}")
        
        # This assertion will FAIL, proving the bug exists
        assert is_member == True, f"Household owner (user {user.id}) should be a member of household {household.id}"
        
        print("✅ TEST PASSED: Owner is correctly a household member")
        
    finally:
        db.close()
        # Clean up
        os.remove("./test.db")

if __name__ == "__main__":
    test_household_owner_becomes_member()