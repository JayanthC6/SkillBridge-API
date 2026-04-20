import os
import sys
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import Base, get_db
from src.main import app
from src.models import Attendance, Batch, BatchInvite, BatchStudent, BatchTrainer, Session, User

TEST_DATABASE_URL = "sqlite:///./test_app.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_app.db"):
        try:
            os.remove("test_app.db")
        except PermissionError:
            pass


@pytest.fixture(autouse=True)
def clear_tables():
    db = TestingSessionLocal()
    try:
        db.query(Attendance).delete()
        db.query(Session).delete()
        db.query(BatchInvite).delete()
        db.query(BatchStudent).delete()
        db.query(BatchTrainer).delete()
        db.query(Batch).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
