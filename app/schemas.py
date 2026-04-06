import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username must be 50 characters or fewer")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username may only contain letters, digits, and underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field cannot be blank")
        if len(v) > 100:
            raise ValueError("Must be 100 characters or fewer")
        return v

    @field_validator("phone_number")
    @classmethod
    def phone_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        cleaned = re.sub(r"[\s\-\(\)\+]", "", v.strip())
        if not cleaned.isdigit():
            raise ValueError("Phone number must contain only digits and common separators")
        if not (7 <= len(cleaned) <= 15):
            raise ValueError("Phone number must be between 7 and 15 digits")
        return v.strip()


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("This field cannot be blank")
            if len(v) > 100:
                raise ValueError("Must be 100 characters or fewer")
        return v

    @field_validator("phone_number")
    @classmethod
    def phone_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        cleaned = re.sub(r"[\s\-\(\)\+]", "", v.strip())
        if not cleaned.isdigit():
            raise ValueError("Phone number must contain only digits and common separators")
        if not (7 <= len(cleaned) <= 15):
            raise ValueError("Phone number must be between 7 and 15 digits")
        return v.strip()


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
