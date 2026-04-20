import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base

class UserRole(str, enum.Enum):
    student = "student"
    trainer = "trainer"
    institution = "institution"
    programme_manager = "programme_manager"
    monitoring_officer = "monitoring_officer"

class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Batch(Base):
    __tablename__ = "batches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class BatchTrainer(Base):
    __tablename__ = "batch_trainers"
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), primary_key=True)
    trainer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)

class BatchStudent(Base):
    __tablename__ = "batch_students"
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), primary_key=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)

class BatchInvite(Base):
    __tablename__ = "batch_invites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"))
    token = Column(String, unique=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"))
    trainer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String, nullable=False)
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    created_at = Column(DateTime, default=datetime.utcnow)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(Enum(AttendanceStatus))
    marked_at = Column(DateTime, default=datetime.utcnow)
