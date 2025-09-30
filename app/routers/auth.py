from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.security import create_access_token, hash_password, verify_password
from ..models import User, UserVerificationToken
from ..services.email import send_verification_email
from ..schemas import (
    LoginRequest,
    ResendVerificationRequest,
    ResendVerificationResponse,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserInfo,
    VerifyEmailRequest,
    VerifyEmailResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

VERIFICATION_EXPIRY_HOURS = 24


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _build_user_info(user: User) -> UserInfo:
    return UserInfo(id=user.id, email=user.email, role=user.role, active=user.active)


def _issue_verification_token(user: User, db: Session) -> UserVerificationToken:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_EXPIRY_HOURS)

    verification = UserVerificationToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    db.add(verification)
    return verification


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)

    existing = db.query(User).filter(func.lower(User.email) == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        active=False,
    )
    db.add(user)
    db.flush()

    verification = _issue_verification_token(user, db)

    db.commit()
    db.refresh(user)

    sent = send_verification_email(user.email, verification.token, verification.expires_at)
    debug_token = verification.token if settings.emit_debug_tokens else None

    return SignupResponse(
        user_id=user.id,
        email=user.email,
        role=user.role,
        active=user.active,
        verification_sent=sent,
        verification_expires_at=verification.expires_at,
        debug_token=debug_token,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)

    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required")

    token = create_access_token(subject=user.id)

    return TokenResponse(access_token=token, user=_build_user_info(user))


@router.post("/verify-email", response_model=VerifyEmailResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    token_entry = (
        db.query(UserVerificationToken)
        .filter(UserVerificationToken.token == payload.token)
        .first()
    )
    if not token_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token")

    if token_entry.used_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already used")

    if token_entry.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired")

    user = token_entry.user
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.active = True
    verified_time = datetime.now(timezone.utc)
    token_entry.used_at = verified_time

    (
        db.query(UserVerificationToken)
        .filter(
            UserVerificationToken.user_id == user.id,
            UserVerificationToken.id != token_entry.id,
            UserVerificationToken.used_at.is_(None),
        )
        .update({UserVerificationToken.used_at: verified_time}, synchronize_session=False)
    )

    db.commit()
    db.refresh(user)

    return VerifyEmailResponse(
        message="Account verified successfully",
        user_id=user.id,
        verified_at=verified_time,
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)

    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.active:
        return ResendVerificationResponse(
            message="Account is already verified",
            verification_sent=False,
            expires_at=None,
            debug_token=None,
        )

    now_utc = datetime.now(timezone.utc)
    (
        db.query(UserVerificationToken)
        .filter(
            UserVerificationToken.user_id == user.id,
            UserVerificationToken.used_at.is_(None),
        )
        .update({UserVerificationToken.used_at: now_utc}, synchronize_session=False)
    )

    verification = _issue_verification_token(user, db)
    db.commit()

    sent = send_verification_email(user.email, verification.token, verification.expires_at)
    debug_token = verification.token if settings.emit_debug_tokens else None

    return ResendVerificationResponse(
        message="Verification email reissued",
        verification_sent=sent,
        expires_at=verification.expires_at,
        debug_token=debug_token,
    )
