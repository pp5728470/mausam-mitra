import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Role
from app.models.user import User
from app.main import app
from app.api.deps import get_current_user

@pytest.fixture(autouse=True)
def unmock_auth(client):
    app.dependency_overrides.pop(get_current_user, None)
    yield


@pytest.mark.asyncio
async def test_register_citizen(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "email": "citizen@example.com",
        "full_name": "Test Citizen",
        "password": "securepassword123"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "citizen@example.com"
    assert data["role"] == "CITIZEN"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "email": "duplicate@example.com",
        "full_name": "Dup",
        "password": "securepassword123"
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "email": "login@example.com",
        "full_name": "Login User",
        "password": "securepassword123"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    # login uses form data
    login_data = {
        "username": "login@example.com",
        "password": "securepassword123"
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "email": "invalid@example.com",
        "full_name": "Invalid",
        "password": "securepassword123"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    login_data = {
        "username": "invalid@example.com",
        "password": "wrongpassword"
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "email": "me@example.com",
        "full_name": "Me User",
        "password": "securepassword123"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    login_data = {
        "username": "me@example.com",
        "password": "securepassword123"
    }
    login_resp = await client.post("/api/v1/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_rbac_citizen_forbidden(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "email": "forbidden@example.com",
        "full_name": "Forbidden",
        "password": "securepassword123"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    login_data = {
        "username": "forbidden@example.com",
        "password": "securepassword123"
    }
    login_resp = await client.post("/api/v1/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    # Try to access a VERIFIER endpoint
    response = await client.get(
        "/api/v1/incidents", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
