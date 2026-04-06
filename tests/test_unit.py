"""
Unit tests — no database required.
"""
import pytest
from pydantic import ValidationError
from app.hashing import hash_password, verify_password
from app.schemas import UserCreate, UserUpdate, UserRead
from datetime import datetime


# ── Hashing ──────────────────────────────────────────────────────────────────

class TestHashing:
    def test_hash_returns_string(self):
        h = hash_password("secret123")
        assert isinstance(h, str)
        assert h != "secret123"

    def test_hash_is_bcrypt(self):
        h = hash_password("secret123")
        assert h.startswith("$2b$")

    def test_verify_correct_password(self):
        h = hash_password("mypassword")
        assert verify_password("mypassword", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("mypassword")
        assert verify_password("wrongpassword", h) is False

    def test_same_password_different_hashes(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses a random salt

    def test_empty_password_hashes(self):
        h = hash_password("")
        assert verify_password("", h) is True
        assert verify_password("x", h) is False


# ── UserCreate schema ─────────────────────────────────────────────────────────

class TestUserCreateSchema:
    def _valid(self, **overrides):
        data = dict(
            username="jane_doe",
            email="jane@example.com",
            first_name="Jane",
            last_name="Doe",
            phone_number="+1-555-0100",
            password="secure123",
        )
        data.update(overrides)
        return UserCreate(**data)

    def test_valid_user(self):
        u = self._valid()
        assert u.username == "jane_doe"
        assert u.email == "jane@example.com"

    def test_short_username_raises(self):
        with pytest.raises(ValidationError, match="at least 3"):
            self._valid(username="ab")

    def test_long_username_raises(self):
        with pytest.raises(ValidationError, match="50 characters"):
            self._valid(username="a" * 51)

    def test_invalid_username_chars(self):
        with pytest.raises(ValidationError, match="letters, digits"):
            self._valid(username="jane doe!")

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            self._valid(email="not-an-email")

    def test_short_password_raises(self):
        with pytest.raises(ValidationError, match="8 characters"):
            self._valid(password="short")

    def test_blank_first_name_raises(self):
        with pytest.raises(ValidationError, match="blank"):
            self._valid(first_name="   ")

    def test_blank_last_name_raises(self):
        with pytest.raises(ValidationError, match="blank"):
            self._valid(last_name="")

    def test_phone_optional(self):
        u = self._valid(phone_number=None)
        assert u.phone_number is None

    def test_phone_empty_string_becomes_none(self):
        u = self._valid(phone_number="")
        assert u.phone_number is None

    def test_phone_invalid_chars(self):
        with pytest.raises(ValidationError, match="digits"):
            self._valid(phone_number="abc-xyz")

    def test_phone_too_short(self):
        with pytest.raises(ValidationError, match="7 and 15 digits"):
            self._valid(phone_number="123")

    def test_username_stripped(self):
        u = self._valid(username="jane_doe")
        assert u.username == "jane_doe"


# ── UserUpdate schema ─────────────────────────────────────────────────────────

class TestUserUpdateSchema:
    def test_empty_update_is_valid(self):
        u = UserUpdate()
        assert u.email is None
        assert u.password is None

    def test_partial_update(self):
        u = UserUpdate(first_name="Janet")
        assert u.first_name == "Janet"
        assert u.last_name is None

    def test_short_password_raises(self):
        with pytest.raises(ValidationError, match="8 characters"):
            UserUpdate(password="abc")

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserUpdate(email="bad-email")


# ── UserRead schema ───────────────────────────────────────────────────────────

class TestUserReadSchema:
    def test_from_attributes(self):
        class FakeUser:
            id = 1
            username = "jane_doe"
            email = "jane@example.com"
            first_name = "Jane"
            last_name = "Doe"
            phone_number = None
            created_at = datetime(2025, 1, 1, 12, 0, 0)

        u = UserRead.model_validate(FakeUser())
        assert u.id == 1
        assert u.username == "jane_doe"
        assert "password" not in u.model_dump()
