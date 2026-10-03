"""
Security and authentication helper utilities for NiveshShakti.
"""
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict, deque
from threading import Lock
import time
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from ..database import get_db
from ..models import User

import bcrypt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_PREHASHED_PASSWORD_PREFIX = "sha256$"
_LOGIN_WINDOW_SECONDS = 900
_LOGIN_MAX_FAILURES = 5
_LOGIN_FAILURES: dict[str, deque[float]] = defaultdict(deque)
_LOGIN_FAILURES_LOCK = Lock()


def _login_bucket_key(email: str, client_host: str) -> str:
    email_digest = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
    return f"{client_host}:{email_digest}"


def ensure_login_allowed(email: str, client_host: str) -> str:
    key = _login_bucket_key(email, client_host)
    now = time.monotonic()
    with _LOGIN_FAILURES_LOCK:
        attempts = _LOGIN_FAILURES[key]
        while attempts and now - attempts[0] >= _LOGIN_WINDOW_SECONDS:
            attempts.popleft()
        if len(attempts) >= _LOGIN_MAX_FAILURES:
            retry_after = max(1, int(_LOGIN_WINDOW_SECONDS - (now - attempts[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )
    return key


def record_failed_login(key: str) -> None:
    with _LOGIN_FAILURES_LOCK:
        _LOGIN_FAILURES[key].append(time.monotonic())


def clear_failed_logins(key: str) -> None:
    with _LOGIN_FAILURES_LOCK:
        _LOGIN_FAILURES.pop(key, None)

# Password hashing directly using bcrypt (immune to passlib's bcrypt 4.0+ wrap bug)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith(_PREHASHED_PASSWORD_PREFIX):
            payload = hashlib.sha256(plain_password.encode("utf-8")).hexdigest().encode("ascii")
            stored_hash = hashed_password[len(_PREHASHED_PASSWORD_PREFIX):].encode("ascii")
        else:
            payload = plain_password.encode("utf-8")[:72]
            stored_hash = hashed_password.encode("utf-8")
        return bcrypt.checkpw(payload, stored_hash)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    payload = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")
    return _PREHASHED_PASSWORD_PREFIX + bcrypt.hashpw(payload, salt).decode("ascii")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
