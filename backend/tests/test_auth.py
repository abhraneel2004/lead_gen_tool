import pytest
from fastapi.testclient import TestClient
from main import app
from tests.test_leads import setup_database

client = TestClient(app)

def test_register_user(setup_database):
    response = client.post(
        "/api/auth/register",
        json={"email": "authuser@example.com", "password": "mypassword1", "full_name": "Auth User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "authuser@example.com"
    assert "id" in data
    assert data["full_name"] == "Auth User"


def test_register_duplicate_user(setup_database):
    # This will fail with 409 as authuser@example.com is already registered by previous test
    response = client.post(
        "/api/auth/register",
        json={"email": "authuser@example.com", "password": "mypassword1", "full_name": "Auth User"}
    )
    assert response.status_code == 409
    assert "Email already registered" in response.json()["detail"]


def test_login_user(setup_database):
    response = client.post(
        "/api/auth/login",
        data={"username": "authuser@example.com", "password": "mypassword1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_user_invalid_password(setup_database):
    response = client.post(
        "/api/auth/login",
        data={"username": "authuser@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
