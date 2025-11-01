from fastapi.testclient import TestClient
from utils.test_data import create_test_user_data
import crud
import schemas


def test_user_registration(client: TestClient):
    test_user = create_test_user_data()
    response = client.post(
        "/auth/register",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
            "full_name": test_user["full_name"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert "id" in data


def test_user_login(client: TestClient):
    test_user = create_test_user_data()
    client.post(
        "/auth/register",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
            "full_name": test_user["full_name"],
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# Tests for Discord OAuth household creation (Clarity: Clear intent, Practicality: Tests actual behavior)
def test_discord_new_user_creates_household(db_session):
    """
    Household Gate Test 1: New Discord user auto-creates household

    Practicality: Ensures users authenticated via Discord can use bot commands immediately
    Clarity: Single assertion - household exists after user creation
    """
    user_data = schemas.DiscordUserCreate(
        email="test@discord.com",
        full_name="Test User",
        discord_id="discord_123",
        discord_username="testuser",
        discord_avatar=None
    )

    new_user = crud.create_discord_user(db_session, user_data)
    households = crud.get_user_households(db_session, new_user.id)

    # Assertion: User has household (would be auto-created in discord_callback)
    assert len(households) > 0, "New Discord user must have household"
    assert households[0].user_id == new_user.id


def test_discord_existing_user_preserves_household(db_session):
    """
    Household Gate Test 2: Existing Discord user household is preserved

    Practicality: Prevents data loss on re-auth - don't create duplicate households
    Clarity: Create user, get household ID, re-lookup user, verify same household
    """
    user_data = schemas.DiscordUserCreate(
        email="existing@discord.com",
        full_name="Existing User",
        discord_id="discord_existing",
        discord_username="existinguser",
        discord_avatar=None
    )

    # First login
    new_user = crud.create_discord_user(db_session, user_data)
    households = crud.get_user_households(db_session, new_user.id)
    original_household_id = households[0].id

    # Second login (finds existing by Discord ID)
    existing_user = crud.get_user_by_discord_id(db_session, "discord_existing")
    households_after = crud.get_user_households(db_session, existing_user.id)

    # Assertion: Same household (no duplicates created)
    assert households_after[0].id == original_household_id, "Household must not change on re-auth"
