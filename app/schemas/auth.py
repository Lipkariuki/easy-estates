from datetime import datetime
from typing import Literal, Optional

import re
from pydantic import BaseModel, Field, field_validator


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class _EmailValidationMixin(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not EMAIL_REGEX.match(email):
            raise ValueError("Invalid email address format")
        return email

    class Config:
        arbitrary_types_allowed = True


class SignupRequest(_EmailValidationMixin):
    password: str = Field(min_length=8)
    role: Literal["owner", "manager"] = "owner"


class SignupResponse(BaseModel):
    user_id: int
    email: str
    role: str
    active: bool
    verification_sent: bool
    verification_expires_at: datetime
    debug_token: Optional[str] = None


class LoginRequest(_EmailValidationMixin):
    password: str


class UserInfo(BaseModel):
    id: int
    email: str
    role: str
    active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class VerifyEmailRequest(BaseModel):
    token: str


class VerifyEmailResponse(BaseModel):
    message: str
    user_id: int
    verified_at: datetime


class ResendVerificationRequest(_EmailValidationMixin):
    pass

class ResendVerificationResponse(BaseModel):
    message: str
    verification_sent: bool
    expires_at: Optional[datetime]
    debug_token: Optional[str] = None
