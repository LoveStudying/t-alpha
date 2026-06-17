from fastapi.testclient import TestClient

from t_alpha.api.deps import get_settings
from t_alpha.config import Settings
from t_alpha.main import app


def override_settings():
    return Settings(
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD="secret",
        ADMIN_TOKEN_SECRET="unit-test-secret",
        ADMIN_SESSION_TTL_SECONDS=3600,
    )


def setup_function():
    app.dependency_overrides[get_settings] = override_settings


def teardown_function():
    app.dependency_overrides.clear()


def test_login_returns_bearer_token_for_valid_credentials():
    client = TestClient(app)

    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "secret"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "admin"


def test_login_rejects_invalid_credentials():
    client = TestClient(app)

    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid username or password"


def test_me_requires_valid_bearer_token():
    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "secret"})
    token = login.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_me_rejects_missing_token():
    client = TestClient(app)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
