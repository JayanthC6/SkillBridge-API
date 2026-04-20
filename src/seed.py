import random
from datetime import date, datetime, time, timedelta

from src.auth_utils import hash_password
from src.database import SessionLocal
from src.models import (
    Attendance,
    AttendanceStatus,
    Batch,
    BatchInvite,
    BatchStudent,
    BatchTrainer,
    Session,
    User,
    UserRole,
)

SEED_PASSWORD = "password123"


def _clear_existing_data(db):
    db.query(Attendance).delete()
    db.query(Session).delete()
    db.query(BatchStudent).delete()
    db.query(BatchTrainer).delete()
    db.query(BatchInvite).delete()
    db.query(Batch).delete()
    db.query(User).delete()
    db.commit()


def _create_users(db):
    hashed_pw = hash_password(SEED_PASSWORD)

    institutions = [
        User(
            name="Institution One",
            email="institution1@skillbridge.test",
            hashed_password=hashed_pw,
            role=UserRole.institution,
        ),
        User(
            name="Institution Two",
            email="institution2@skillbridge.test",
            hashed_password=hashed_pw,
            role=UserRole.institution,
        ),
    ]

    trainers = [
        User(
            name=f"Trainer {idx}",
            email=f"trainer{idx}@skillbridge.test",
            hashed_password=hashed_pw,
            role=UserRole.trainer,
        )
        for idx in range(1, 5)
    ]

    students = [
        User(
            name=f"Student {idx}",
            email=f"student{idx}@skillbridge.test",
            hashed_password=hashed_pw,
            role=UserRole.student,
        )
        for idx in range(1, 16)
    ]

    programme_manager = User(
        name="Programme Manager",
        email="programme.manager@skillbridge.test",
        hashed_password=hashed_pw,
        role=UserRole.programme_manager,
    )

    monitoring_officer = User(
        name="Monitoring Officer",
        email="monitoring.officer@skillbridge.test",
        hashed_password=hashed_pw,
        role=UserRole.monitoring_officer,
    )

    all_users = institutions + trainers + students + [programme_manager, monitoring_officer]
    db.add_all(all_users)
    db.commit()
    for user in all_users:
        db.refresh(user)

    return {
        "institutions": institutions,
        "trainers": trainers,
        "students": students,
        "programme_manager": programme_manager,
        "monitoring_officer": monitoring_officer,
        "all_users": all_users,
    }


def _create_batches(db, institutions):
    batches = [
        Batch(name="Python Backend - A", institution_id=institutions[0].id),
        Batch(name="Data Analytics - B", institution_id=institutions[0].id),
        Batch(name="Cloud Computing - C", institution_id=institutions[1].id),
    ]
    db.add_all(batches)
    db.commit()
    for batch in batches:
        db.refresh(batch)
    return batches


def _create_batch_assignments(db, batches, trainers, students):
    trainer_map = {
        batches[0].id: [trainers[0], trainers[1]],
        batches[1].id: [trainers[1], trainers[2]],
        batches[2].id: [trainers[2], trainers[3]],
    }

    student_slices = {
        batches[0].id: students[0:5],
        batches[1].id: students[5:10],
        batches[2].id: students[10:15],
    }

    trainer_links = []
    student_links = []

    for batch_id, batch_trainers in trainer_map.items():
        for trainer in batch_trainers:
            trainer_links.append(BatchTrainer(batch_id=batch_id, trainer_id=trainer.id))

    for batch_id, batch_students in student_slices.items():
        for student in batch_students:
            student_links.append(BatchStudent(batch_id=batch_id, student_id=student.id))

    db.add_all(trainer_links + student_links)
    db.commit()

    return trainer_map, student_slices


def _create_sessions(db, batches, trainer_map):
    sessions = []
    base_date = date.today() - timedelta(days=7)

    distribution = [
        (batches[0], 3),
        (batches[1], 3),
        (batches[2], 2),
    ]

    session_counter = 1
    for batch, count in distribution:
        primary_trainer = trainer_map[batch.id][0]
        for idx in range(count):
            sessions.append(
                Session(
                    batch_id=batch.id,
                    trainer_id=primary_trainer.id,
                    title=f"Session {session_counter}: Topic {idx + 1}",
                    date=base_date + timedelta(days=session_counter),
                    start_time=time(hour=9, minute=0),
                    end_time=time(hour=11, minute=0),
                )
            )
            session_counter += 1

    db.add_all(sessions)
    db.commit()
    for session in sessions:
        db.refresh(session)
    return sessions


def _create_attendance(db, sessions, student_slices):
    rng = random.Random(42)
    statuses = [AttendanceStatus.present, AttendanceStatus.absent, AttendanceStatus.late]
    weights = [0.7, 0.15, 0.15]

    records = []
    for session in sessions:
        students = student_slices[session.batch_id]
        for student in students:
            records.append(
                Attendance(
                    session_id=session.id,
                    student_id=student.id,
                    status=rng.choices(statuses, weights=weights, k=1)[0],
                    marked_at=datetime.utcnow(),
                )
            )

    db.add_all(records)
    db.commit()
    return records


def _print_account_summary(all_users):
    print("\n=== SkillBridge Seed Accounts ===")
    print(f"{'Role':<22} {'Email':<40} {'Password'}")
    print("-" * 80)
    for user in sorted(all_users, key=lambda u: (u.role.value, u.email)):
        print(f"{user.role.value:<22} {user.email:<40} {SEED_PASSWORD}")
    print("-" * 80)
    print(f"Total accounts: {len(all_users)}\n")


def seed():
    db = SessionLocal()
    try:
        _clear_existing_data(db)
        users = _create_users(db)
        batches = _create_batches(db, users["institutions"])
        trainer_map, student_slices = _create_batch_assignments(
            db, batches, users["trainers"], users["students"]
        )
        sessions = _create_sessions(db, batches, trainer_map)
        attendance_records = _create_attendance(db, sessions, student_slices)

        print("Seed complete:")
        print(f"- Users: {len(users['all_users'])}")
        print(f"- Batches: {len(batches)}")
        print(f"- Sessions: {len(sessions)}")
        print(f"- Attendance records: {len(attendance_records)}")
        _print_account_summary(users["all_users"])
    finally:
        db.close()


if __name__ == "__main__":
    seed()
