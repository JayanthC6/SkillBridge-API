from src.models import UserRole
from datetime import date, datetime, time
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from src.models import AttendanceStatus

class SignupRequest(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=6)
    role: UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class MonitoringTokenRequest(BaseModel):
    key: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class BatchCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    institution_id: UUID

class BatchResponse(BaseModel):
    id: UUID
    name: str
    institution_id: UUID
    created_at: datetime

class BatchInviteResponse(BaseModel):
    token: str
    batch_id: UUID
    expires_at: datetime
    used: bool

class BatchJoinRequest(BaseModel):
    token: str = Field(min_length=1)

class BatchJoinResponse(BaseModel):
    batch_id: UUID
    student_id: UUID
    joined: bool

class SessionCreateRequest(BaseModel):
    batch_id: UUID
    title: str = Field(min_length=1)
    date: date
    start_time: time
    end_time: time

class SessionResponse(BaseModel):
    id: UUID
    batch_id: UUID
    trainer_id: UUID
    title: str
    date: date
    start_time: time
    end_time: time
    created_at: datetime

class AttendanceMarkRequest(BaseModel):
    session_id: UUID
    status: AttendanceStatus

class AttendanceResponse(BaseModel):
    id: UUID
    session_id: UUID
    student_id: UUID
    status: AttendanceStatus
    marked_at: datetime

class SessionAttendanceResponse(BaseModel):
    session_id: UUID
    items: list[AttendanceResponse]

class BatchSummaryResponse(BaseModel):
    batch_id: UUID
    total_trainers: int
    total_students: int
    total_sessions: int
    total_attendance_records: int

class InstitutionSummaryResponse(BaseModel):
    institution_id: UUID
    total_batches: int
    total_trainers: int
    total_students: int
    total_sessions: int
    total_attendance_records: int

class ProgrammeSummaryResponse(BaseModel):
    total_institutions: int
    total_batches: int
    total_trainers: int
    total_students: int
    total_sessions: int
    total_attendance_records: int
