from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.auth_utils import create_access_token, get_current_user, verify_password, hash_password
from src.config import MONITORING_API_KEY
from src.database import get_db
from src.models import User, UserRole
from src.schemas import LoginRequest, MonitoringTokenRequest, SignupRequest, TokenResponse

router = APIRouter()


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    return parts[1]


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email already exists",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"user_id": str(user.id), "role": user.role.value},
        expires_delta=timedelta(hours=24),
    )
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        data={"user_id": str(user.id), "role": user.role.value},
        expires_delta=timedelta(hours=24),
    )
    return TokenResponse(access_token=access_token)


@router.post("/monitoring-token", response_model=TokenResponse)
def create_monitoring_token(
    payload: MonitoringTokenRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    token = _extract_bearer_token(authorization)
    user = get_current_user(token, db)

    if user.role != UserRole.monitoring_officer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User role is not monitoring_officer",
        )

    if payload.key != MONITORING_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid monitoring API key",
        )

    scoped_token = create_access_token(
        data={
            "user_id": str(user.id),
            "role": UserRole.monitoring_officer.value,
            "scope": "monitoring_only",
        },
        expires_delta=timedelta(hours=1),
    )
    return TokenResponse(access_token=scoped_token)
