"""
Test for N+1 query optimization in get_user_items and get_user_locations functions
"""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import event, create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import crud
import models
import schemas
from utils.test_data import create_test_user_data

# Query counter for testing N+1 queries
query_count = 0

def count_queries(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_n_plus_one.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestNPlusOneOptimization:
    """Test N+1 query optimizations"""
    
    def setup_method(self):
        """Setup test database with sample data"""
        global query_count
        query_count = 0
        
        # Create tables
        models.Base.metadata.create_all(bind=engine)
        
        self.db = TestingSessionLocal()
        
        # Enable query counting
        event.listen(engine, "before_cursor_execute", count_queries)
        
        # Create test data using existing CRUD functions
        # Create test user
        user_data = create_test_user_data()
        self.user = models.User(
            email=user_data["email"],
            hashed_password="hashedpass",
            full_name=user_data["full_name"],
            is_verified=True
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)
        
        # Create household 1
        self.household1 = crud.create_household(
            self.db, 
            schemas.HouseholdCreate(name="Household 1", description="Test household 1"), 
            self.user.id
        )
        
        # Create household 2  
        self.household2 = crud.create_household(
            self.db, 
            schemas.HouseholdCreate(name="Household 2", description="Test household 2"), 
            self.user.id
        )
        
        # Get locations (default locations are created by create_household)
        h1_locations = crud.get_household_locations(self.db, self.household1.id)
        h2_locations = crud.get_household_locations(self.db, self.household2.id)
        
        # Create items in household 1 locations
        for loc in h1_locations:
            crud.create_item(self.db, schemas.ItemCreate(name=f"Item1-{loc.name}", description="Test item"), loc.id, self.user.id)
            crud.create_item(self.db, schemas.ItemCreate(name=f"Item2-{loc.name}", description="Test item"), loc.id, self.user.id)
        
        # Create items in household 2 locations  
        for loc in h2_locations:
            crud.create_item(self.db, schemas.ItemCreate(name=f"Item1-{loc.name}", description="Test item"), loc.id, self.user.id)
            crud.create_item(self.db, schemas.ItemCreate(name=f"Item2-{loc.name}", description="Test item"), loc.id, self.user.id)
    
    def teardown_method(self):
        """Clean up test database"""
        event.remove(engine, "before_cursor_execute", count_queries)
        self.db.close()
        models.Base.metadata.drop_all(bind=engine)
    
    def test_get_user_items_query_efficiency(self):
        """Test that get_user_items uses minimal queries"""
        global query_count
        query_count = 0
        
        # Call the optimized function
        items = crud.get_user_items(self.db, self.user.id)
        
        # Verify we got all items (12 total)
        assert len(items) == 12, f"Expected 12 items, got {len(items)}"
        
        # Verify query efficiency - should be 1 main query + minimal relationship loads
        # Should be significantly less than the old N+1 approach which would be 1 + 2 + 6 = 9 queries
        assert query_count <= 3, f"Too many queries: {query_count}, expected <= 3"
        
        print(f"✅ get_user_items executed with {query_count} queries (optimized)")
    
    def test_get_user_locations_query_efficiency(self):
        """Test that get_user_locations uses minimal queries"""
        global query_count
        query_count = 0
        
        # Call the optimized function
        locations = crud.get_user_locations(self.db, self.user.id)
        
        # Verify we got all locations (6 total)
        assert len(locations) == 6, f"Expected 6 locations, got {len(locations)}"
        
        # Verify query efficiency - should be 1-2 queries
        assert query_count <= 2, f"Too many queries: {query_count}, expected <= 2"
        
        print(f"✅ get_user_locations executed with {query_count} queries (optimized)")
    
    def test_get_user_items_data_correctness(self):
        """Test that optimized get_user_items returns correct data"""
        items = crud.get_user_items(self.db, self.user.id)
        
        # Verify we have items from both households
        household_ids = {item.household_id for item in items}
        assert self.household1.id in household_ids
        assert self.household2.id in household_ids
        
        # Verify relationships are properly loaded
        for item in items:
            assert hasattr(item, 'location'), "Location relationship not loaded"
            assert hasattr(item.location, 'household'), "Household relationship not loaded" 
            assert hasattr(item, 'added_by'), "added_by relationship not loaded"
            assert item.added_by.id == self.user.id, "Incorrect user relationship"
        
        print("✅ get_user_items returns correct data with proper relationships")
    
    def test_get_user_locations_data_correctness(self):
        """Test that optimized get_user_locations returns correct data"""
        locations = crud.get_user_locations(self.db, self.user.id)
        
        # Verify we have locations from both households
        household_ids = {loc.household.id for loc in locations}
        assert self.household1.id in household_ids
        assert self.household2.id in household_ids
        
        # Verify relationships are properly loaded
        for location in locations:
            assert hasattr(location, 'household'), "Household relationship not loaded"
            assert location.household.id in [self.household1.id, self.household2.id]
        
        print("✅ get_user_locations returns correct data with proper relationships")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])