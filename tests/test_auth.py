import pytest
from fastapi import HTTPException
from app.core.auth import get_current_user
from app.db.models import User

async def test_get_current_user_success(db_session):
    """Test getting current user with valid token"""
    # Create a test user
    user = User(chat_id="123", name="Test User", role="student")
    db_session.add(user)
    db_session.commit()
    
    # Get current user
    result = await get_current_user(token="123", db=db_session)
    assert result.chat_id == "123"
    assert result.name == "Test User"
    assert result.role == "student"

async def test_get_current_user_not_found(db_session):
    """Test getting current user with invalid token"""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="invalid", db=db_session)
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials" 