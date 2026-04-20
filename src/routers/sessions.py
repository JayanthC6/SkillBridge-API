from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.auth_utils import get_current_user_dependency
from src.database import get_db
from src.models import Attendance, Batch, Session as BatchSession, User, UserRole
from src.schemas import (
    AttendanceResponse,
    SessionAttendanceResponse,
    SessionCreateRequest,
    SessionResponse,
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


@router.post("/sessions", response_model=SessionResponse)
def create_session(
    payload: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.trainer)),
):
    batch = db.query(Batch).filter(Batch.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    session = BatchSession(
        batch_id=payload.batch_id,
        trainer_id=current_user.id,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(session)
    try:
        db.commit()
        db.refresh(session)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not create session",
        ) from exc

    return SessionResponse(
        id=session.id,
        batch_id=session.batch_id,
        trainer_id=session.trainer_id,
        title=session.title,
        date=session.date,
        start_time=session.start_time,
        end_time=session.end_time,
        created_at=session.created_at,
    )


@router.get("/sessions/{id}/attendance", response_model=SessionAttendanceResponse)
def get_session_attendance(
    id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.trainer)),
):
    session = db.query(BatchSession).filter(BatchSession.id == id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    attendance_rows = db.query(Attendance).filter(Attendance.session_id == session.id).all()
    items = [
        AttendanceResponse(
            id=row.id,
            session_id=row.session_id,
            student_id=row.student_id,
            status=row.status,
            marked_at=row.marked_at,
        )
        for row in attendance_rows
    ]
    return SessionAttendanceResponse(session_id=session.id, items=items)
