from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth_utils import get_current_user_dependency
from src.database import get_db
from src.models import Attendance, Batch, BatchStudent, BatchTrainer, Session as BatchSession, User, UserRole
from src.schemas import BatchSummaryResponse, InstitutionSummaryResponse, ProgrammeSummaryResponse

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


@router.get("/batches/{id}/summary", response_model=BatchSummaryResponse)
def get_batch_summary(
    id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.institution)),
):
    batch = db.query(Batch).filter(Batch.id == id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    session_ids = [row.id for row in db.query(BatchSession.id).filter(BatchSession.batch_id == id).all()]
    attendance_count = 0
    if session_ids:
        attendance_count = db.query(Attendance).filter(Attendance.session_id.in_(session_ids)).count()

    return BatchSummaryResponse(
        batch_id=batch.id,
        total_trainers=db.query(BatchTrainer).filter(BatchTrainer.batch_id == id).count(),
        total_students=db.query(BatchStudent).filter(BatchStudent.batch_id == id).count(),
        total_sessions=len(session_ids),
        total_attendance_records=attendance_count,
    )


@router.get("/institutions/{id}/summary", response_model=InstitutionSummaryResponse)
def get_institution_summary(
    id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.programme_manager)),
):
    institution = db.query(User).filter(User.id == id).first()
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    batches = db.query(Batch.id).filter(Batch.institution_id == id).all()
    batch_ids = [row.id for row in batches]
    session_ids = (
        [row.id for row in db.query(BatchSession.id).filter(BatchSession.batch_id.in_(batch_ids)).all()]
        if batch_ids
        else []
    )

    total_trainers = (
        db.query(BatchTrainer).filter(BatchTrainer.batch_id.in_(batch_ids)).count() if batch_ids else 0
    )
    total_students = (
        db.query(BatchStudent).filter(BatchStudent.batch_id.in_(batch_ids)).count() if batch_ids else 0
    )
    total_attendance = (
        db.query(Attendance).filter(Attendance.session_id.in_(session_ids)).count() if session_ids else 0
    )

    return InstitutionSummaryResponse(
        institution_id=id,
        total_batches=len(batch_ids),
        total_trainers=total_trainers,
        total_students=total_students,
        total_sessions=len(session_ids),
        total_attendance_records=total_attendance,
    )


@router.get("/programme/summary", response_model=ProgrammeSummaryResponse)
def get_programme_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.programme_manager)),
):
    batch_ids = [row.id for row in db.query(Batch.id).all()]
    session_ids = [row.id for row in db.query(BatchSession.id).all()]

    return ProgrammeSummaryResponse(
        total_institutions=db.query(User).filter(User.role == UserRole.institution).count(),
        total_batches=len(batch_ids),
        total_trainers=db.query(BatchTrainer).count(),
        total_students=db.query(BatchStudent).count(),
        total_sessions=len(session_ids),
        total_attendance_records=db.query(Attendance).count(),
    )
