from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.auth_utils import get_current_user_dependency
from src.database import get_db
from src.models import Batch, BatchInvite, BatchStudent, BatchTrainer, User, UserRole
from src.schemas import (
    BatchCreateRequest,
    BatchInviteResponse,
    BatchJoinRequest,
    BatchJoinResponse,
    BatchResponse,
)

router = APIRouter()


def require_roles(*allowed_roles: UserRole):
    def _dependency(current_user: User = Depends(get_current_user_dependency)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to perform this action",
            )
        return current_user

    return _dependency


@router.post("/batches", response_model=BatchResponse)
def create_batch(
    payload: BatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.trainer, UserRole.institution)),
):
    institution = db.query(User).filter(User.id == payload.institution_id).first()
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    batch = Batch(id=uuid4(), name=payload.name, institution_id=payload.institution_id)
    db.add(batch)

    if current_user.role == UserRole.trainer:
        db.add(BatchTrainer(batch_id=batch.id, trainer_id=current_user.id))

    try:
        db.commit()
        db.refresh(batch)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not create batch",
        ) from exc

    return BatchResponse(
        id=batch.id,
        name=batch.name,
        institution_id=batch.institution_id,
        created_at=batch.created_at,
    )


@router.post("/batches/{id}/invite", response_model=BatchInviteResponse)
def create_batch_invite(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.trainer)),
):
    batch = db.query(Batch).filter(Batch.id == id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    token = str(uuid4())
    invite = BatchInvite(
        batch_id=batch.id,
        token=token,
        created_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        used=False,
    )
    db.add(invite)
    try:
        db.commit()
        db.refresh(invite)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not create invite",
        ) from exc

    return BatchInviteResponse(
        token=invite.token,
        batch_id=invite.batch_id,
        expires_at=invite.expires_at,
        used=bool(invite.used),
    )


@router.post("/batches/join", response_model=BatchJoinResponse)
def join_batch(
    payload: BatchJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
):
    invite = db.query(BatchInvite).filter(BatchInvite.token == payload.token).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")

    now = datetime.now(timezone.utc)
    invite_expiry = invite.expires_at
    if invite_expiry and invite_expiry.tzinfo is None:
        invite_expiry = invite_expiry.replace(tzinfo=timezone.utc)

    if invite.used or (invite_expiry and invite_expiry < now):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invite is invalid or expired",
        )

    batch = db.query(Batch).filter(Batch.id == invite.batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    existing_membership = (
        db.query(BatchStudent)
        .filter(BatchStudent.batch_id == batch.id, BatchStudent.student_id == current_user.id)
        .first()
    )
    if existing_membership:
        invite.used = True
        db.add(invite)
        try:
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not process invite",
            ) from exc
        return BatchJoinResponse(batch_id=batch.id, student_id=current_user.id, joined=True)

    db.add(BatchStudent(batch_id=batch.id, student_id=current_user.id))
    invite.used = True
    db.add(invite)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not join batch",
        ) from exc

    return BatchJoinResponse(batch_id=batch.id, student_id=current_user.id, joined=True)
