from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.auth_utils import decode_token, extract_bearer_token, get_current_user, get_current_user_dependency
from src.database import get_db
from src.models import Attendance, BatchStudent, Session as BatchSession, User, UserRole
from src.schemas import AttendanceMarkRequest, AttendanceResponse

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


def get_monitoring_scoped_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = extract_bearer_token(authorization)
    payload = decode_token(token)
    if payload.get("scope") != "monitoring_only":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Scoped monitoring token required",
        )
    user = get_current_user(token, db)
    if user.role != UserRole.monitoring_officer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Monitoring officer role required",
        )
    return user


@router.post("/attendance/mark", response_model=AttendanceResponse)
def mark_attendance(
    payload: AttendanceMarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
):
    session = db.query(BatchSession).filter(BatchSession.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    enrollment = (
        db.query(BatchStudent)
        .filter(
            BatchStudent.batch_id == session.batch_id,
            BatchStudent.student_id == current_user.id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student is not enrolled in this batch",
        )

    attendance = (
        db.query(Attendance)
        .filter(Attendance.session_id == session.id, Attendance.student_id == current_user.id)
        .first()
    )
    if attendance:
        attendance.status = payload.status
        db.add(attendance)
    else:
        attendance = Attendance(
            session_id=session.id,
            student_id=current_user.id,
            status=payload.status,
        )
        db.add(attendance)

    try:
        db.commit()
        db.refresh(attendance)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not mark attendance",
        ) from exc

    return AttendanceResponse(
        id=attendance.id,
        session_id=attendance.session_id,
        student_id=attendance.student_id,
        status=attendance.status,
        marked_at=attendance.marked_at,
    )


@router.get("/monitoring/attendance", response_model=list[AttendanceResponse])
def get_monitoring_attendance(
    _: User = Depends(get_monitoring_scoped_user),
    db: Session = Depends(get_db),
):
    rows = db.query(Attendance).all()
    return [
        AttendanceResponse(
            id=row.id,
            session_id=row.session_id,
            student_id=row.student_id,
            status=row.status,
            marked_at=row.marked_at,
        )
        for row in rows
    ]


@router.api_route("/monitoring/attendance", methods=["POST", "PUT", "PATCH", "DELETE"])
def monitoring_attendance_method_not_allowed():
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method not allowed",
    )
