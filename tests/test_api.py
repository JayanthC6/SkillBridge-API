from datetime import date
from datetime import time as dt_time
import pytest
from jose import jwt
from src.auth_utils import hash_password
from src.config import SECRET_KEY
from src.models import Batch, BatchStudent, Session, User, UserRole

ALGORITHM = "HS256"
pytestmark = pytest.mark.asyncio

def _decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

async def test_student_signup_and_login(client):
    signup_payload = {
        "name": "Student Test",
        "email": "student.signup@test.com",
        "password": "password123",
        "role": "student",
    }
    signup_response = await client.post("/auth/signup", json=signup_payload)
    assert signup_response.status_code in (200, 201)
    signup_token = signup_response.json().get("access_token")
    assert signup_token
    assert "user_id" in _decode_token(signup_token)

    login_payload = {"email": signup_payload["email"], "password": signup_payload["password"]}
    login_response = await client.post("/auth/login", json=login_payload)
    assert login_response.status_code in (200, 201)
    login_token = login_response.json().get("access_token")
    assert login_token
    decoded = _decode_token(login_token)
    assert decoded.get("role") == "student"
    assert decoded.get("user_id")

async def test_trainer_create_session(client):
    institution_signup = await client.post(
        "/auth/signup",
        json={
            "name": "Inst One",
            "email": "institution.one@test.com",
            "password": "password123",
            "role": "institution",
        },
    )
    institution_token = institution_signup.json()["access_token"]
    institution_id = _decode_token(institution_token)["user_id"]
    trainer_signup = await client.post(
        "/auth/signup",
        json={
            "name": "Trainer One",
            "email": "trainer.one@test.com",
            "password": "password123",
            "role": "trainer",
        },
    )
    assert trainer_signup.status_code in (200, 201)

    trainer_login = await client.post(
        "/auth/login",
        json={"email": "trainer.one@test.com", "password": "password123"},
    )
    trainer_token = trainer_login.json()["access_token"]

    batch_response = await client.post(
        "/batches",
        json={"name": "Backend Batch", "institution_id": institution_id},
        headers={"Authorization": f"Bearer {institution_token}"},
    )
    assert batch_response.status_code in (200, 201)
    batch_id = batch_response.json()["id"]

    session_payload = {
        "batch_id": batch_id,
        "title": "Intro to API",
        "date": str(date.today()),
        "start_time": "09:00:00",
        "end_time": "10:00:00",
    }
    session_response = await client.post(
        "/sessions",
        json=session_payload,
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert session_response.status_code in (200, 201)

async def test_student_mark_attendance(client, db_session):
    db = db_session
    institution = User(
        name="Institution For Attendance",
        email="institution.attendance@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.institution,
    )
    trainer = User(
        name="Trainer Attendance",
        email="trainer.attendance@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.trainer,
    )
    student = User(
        name="Student Attendance",
        email="student.attendance@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.student,
    )
    db.add_all([institution, trainer, student])
    db.commit()
    db.refresh(institution)
    db.refresh(trainer)
    db.refresh(student)

    batch = Batch(name="Attendance Batch", institution_id=institution.id)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    session = Session(
        batch_id=batch.id,
        trainer_id=trainer.id,
        title="Attendance Session",
        date=date.today(),
        start_time=dt_time(hour=9, minute=0),
        end_time=dt_time(hour=10, minute=0),
    )
    db.add(session)
    db.add(BatchStudent(batch_id=batch.id, student_id=student.id))
    db.commit()
    db.refresh(session)
    session_id = str(session.id)

    login_response = await client.post(
        "/auth/login",
        json={"email": "student.attendance@test.com", "password": "password123"},
    )
    assert login_response.status_code in (200, 201)
    student_token = login_response.json()["access_token"]

    mark_response = await client.post(
        "/attendance/mark",
        json={"session_id": session_id, "status": "present"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert mark_response.status_code in (200, 201)

async def test_monitoring_post_returns_405(client):
    response = await client.post("/monitoring/attendance", json={})
    assert response.status_code == 405

async def test_no_token_returns_401(client):
    response = await client.get("/programme/summary")
    assert response.status_code == 401
