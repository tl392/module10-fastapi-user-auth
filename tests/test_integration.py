"""
Integration tests — require a real PostgreSQL database.
Set DATABASE_URL env var or use the default (matches GitHub Actions service).
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from main import app

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/userdb",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Truncate users table before each test for isolation."""
    yield
    from app.models import User
    with TestingSessionLocal() as session:
        session.query(User).delete()
        session.commit()


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _user_payload(**overrides):
    data = dict(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        phone_number="+1-555-0100",
        password="securepass",
    )
    data.update(overrides)
    return data


# ── Create ────────────────────────────────────────────────────────────────────

class TestCreateUser:
    def test_create_success(self, client):
        r = client.post("/users/", json=_user_payload())
        assert r.status_code == 201
        body = r.json()
        assert body["username"] == "testuser"
        assert "password_hash" not in body
        assert "password" not in body
        assert "id" in body
        assert "created_at" in body

    def test_create_duplicate_username(self, client):
        client.post("/users/", json=_user_payload())
        r = client.post("/users/", json=_user_payload(email="other@example.com"))
        assert r.status_code == 400
        assert "Username" in r.json()["detail"]

    def test_create_duplicate_email(self, client):
        client.post("/users/", json=_user_payload())
        r = client.post("/users/", json=_user_payload(username="other_user"))
        assert r.status_code == 400
        assert "Email" in r.json()["detail"]

    def test_create_invalid_email_format(self, client):
        r = client.post("/users/", json=_user_payload(email="not-an-email"))
        assert r.status_code == 422

    def test_create_short_password(self, client):
        r = client.post("/users/", json=_user_payload(password="short"))
        assert r.status_code == 422

    def test_create_blank_first_name(self, client):
        r = client.post("/users/", json=_user_payload(first_name="   "))
        assert r.status_code == 422

    def test_create_no_phone(self, client):
        r = client.post("/users/", json=_user_payload(phone_number=None))
        assert r.status_code == 201
        assert r.json()["phone_number"] is None

    def test_create_returns_correct_name(self, client):
        r = client.post("/users/", json=_user_payload(first_name="Jane", last_name="Doe"))
        assert r.status_code == 201
        assert r.json()["first_name"] == "Jane"
        assert r.json()["last_name"] == "Doe"


# ── Read ──────────────────────────────────────────────────────────────────────

class TestReadUser:
    def test_read_existing(self, client):
        created = client.post("/users/", json=_user_payload()).json()
        r = client.get(f"/users/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_read_not_found(self, client):
        r = client.get("/users/99999")
        assert r.status_code == 404

    def test_list_users_empty(self, client):
        r = client.get("/users/")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_users_populated(self, client):
        client.post("/users/", json=_user_payload())
        client.post("/users/", json=_user_payload(username="user2", email="u2@x.com"))
        r = client.get("/users/")
        assert r.status_code == 200
        assert len(r.json()) == 2


# ── Update ────────────────────────────────────────────────────────────────────

class TestUpdateUser:
    def test_update_first_name(self, client):
        uid = client.post("/users/", json=_user_payload()).json()["id"]
        r = client.put(f"/users/{uid}", json={"first_name": "Updated"})
        assert r.status_code == 200
        assert r.json()["first_name"] == "Updated"

    def test_update_phone(self, client):
        uid = client.post("/users/", json=_user_payload()).json()["id"]
        r = client.put(f"/users/{uid}", json={"phone_number": "+44-20-1234-5678"})
        assert r.status_code == 200

    def test_update_password_hashed(self, client):
        uid = client.post("/users/", json=_user_payload()).json()["id"]
        r = client.put(f"/users/{uid}", json={"password": "newpassword1"})
        assert r.status_code == 200
        assert "password_hash" not in r.json()

    def test_update_duplicate_email(self, client):
        uid1 = client.post("/users/", json=_user_payload()).json()["id"]
        client.post("/users/", json=_user_payload(username="user2", email="u2@x.com"))
        r = client.put(f"/users/{uid1}", json={"email": "u2@x.com"})
        assert r.status_code == 400

    def test_update_not_found(self, client):
        r = client.put("/users/99999", json={"first_name": "Ghost"})
        assert r.status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────

class TestDeleteUser:
    def test_delete_existing(self, client):
        uid = client.post("/users/", json=_user_payload()).json()["id"]
        r = client.delete(f"/users/{uid}")
        assert r.status_code == 204
        assert client.get(f"/users/{uid}").status_code == 404

    def test_delete_not_found(self, client):
        r = client.delete("/users/99999")
        assert r.status_code == 404

    def test_delete_removes_from_list(self, client):
        uid = client.post("/users/", json=_user_payload()).json()["id"]
        client.delete(f"/users/{uid}")
        r = client.get("/users/")
        assert r.json() == []
