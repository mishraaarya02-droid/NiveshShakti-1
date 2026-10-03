"""
Authentication router for NiveshShakti.
Endpoints:
- POST /auth/register
- POST /auth/login
- GET /auth/me
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, AuditLog
from ..schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserPreferencesUpdateRequest,
    TokenResponse,
    UserProfileResponse,
)
from ..core.security import (
    clear_failed_logins,
    create_access_token,
    ensure_login_allowed,
    get_current_user,
    get_password_hash,
    record_failed_login,
    verify_password,
)

router = APIRouter()

@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    hashed_pw = get_password_hash(req.password)
    user = User(
        email=req.email.lower(),
        hashed_password=hashed_pw,
        language=req.language,
        knowledge_level=req.knowledge_level
    )
    db.add(user)
    db.flush()

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="USER_REGISTERED",
        details={"email": user.email, "language": user.language.value}
    )
    db.add(audit)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    client_host = request.client.host if request.client else "unknown"
    rate_limit_key = ensure_login_allowed(req.email, client_host)
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        record_failed_login(rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    clear_failed_logins(rate_limit_key)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is disabled")

    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="USER_LOGIN_SUCCESS",
        details={"email": user.email}
    )
    db.add(audit)
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserProfileResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/preferences", response_model=UserProfileResponse)
def update_user_preferences(
    req: UserPreferencesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.language = req.language
    current_user.knowledge_level = req.knowledge_level
    db.commit()
    db.refresh(current_user)
    return current_user
