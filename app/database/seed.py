"""Seed the database with a test admin, a test user and a few sample tasks.

Run from the project root:   python -m app.database.seed

LOCAL TESTING ONLY: these credentials are public (they appear in the README).
Safe to run many times: existing rows are skipped, never duplicated.
"""
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.database.session import SessionLocal
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole

# ---------- The data to insert ----------

SEED_USERS = [
    {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "Admin@12345",
        "role": UserRole.ADMIN,
    },
    {
        "name": "Regular User",
        "email": "user@example.com",
        "password": "User@12345",
        "role": UserRole.USER,
    },
]

# email of the owner -> list of (title, description, status)
SEED_TASKS = {
    "user@example.com": [
        ("Write project report", "Summarise the quarterly numbers for the team.", TaskStatus.PENDING),
        ("Fix login page bug", "Users on mobile cannot see the password field.", TaskStatus.IN_PROGRESS),
        ("Update README", "Document the setup steps and API endpoints.", TaskStatus.COMPLETED),
    ],
    "admin@example.com": [
        ("Review pending tasks", "Check every open task and update its status.", TaskStatus.TESTING),
        ("Plan next sprint", None, TaskStatus.PENDING),  # description is optional
    ],
}


# ---------- Helpers ----------

def get_or_create_user(db: Session, data: dict) -> tuple[User, bool]:
    """Return (user, created). Looks the user up by email first."""
    user = db.execute(
        select(User).where(User.email == data["email"])
    ).scalar_one_or_none()
    if user is not None:
        return user, False  # already there: leave it untouched

    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=hash_password(data["password"]),  # hashed, never plain
        role=data["role"].value,  # enum -> plain string, e.g. "admin"
    )
    db.add(user)
    db.flush()  # sends the INSERT so user.id exists, but does not commit yet
    return user, True


def create_task_if_missing(
    db: Session, owner: User, title: str, description, status: TaskStatus
) -> bool:
    """Return True if a task was added. A task already exists if the same owner
    has one with the same title."""
    exists = db.execute(
        select(Task.id).where(Task.user_id == owner.id, Task.title == title)
    ).first()
    if exists is not None:
        return False

    db.add(
        Task(
            user_id=owner.id,
            title=title,
            description=description,
            status=status.value,
        )
    )
    return True


# ---------- Main ----------

def seed() -> None:
    print("Seeding database...")
    db = SessionLocal()
    users_created = 0
    tasks_created = 0
    try:
        owners: dict[str, User] = {}

        for data in SEED_USERS:
            user, created = get_or_create_user(db, data)
            owners[data["email"]] = user
            if created:
                users_created += 1
                print(f"  [created] user  {data['email']} ({data['role'].value})")
            else:
                print(f"  [skipped] user  {data['email']} already exists")
                if user.role != data["role"].value:
                    print(f"            WARNING: its role is '{user.role}', expected '{data['role'].value}'")

        for email, tasks in SEED_TASKS.items():
            for title, description, status in tasks:
                if create_task_if_missing(db, owners[email], title, description, status):
                    tasks_created += 1
                    print(f"  [created] task  '{title}' ({status.value}) for {email}")
                else:
                    print(f"  [skipped] task  '{title}' for {email} already exists")

        db.commit()  # everything becomes permanent here, all at once
    except SQLAlchemyError as exc:
        db.rollback()  # undo the partial work
        # Print only the error type: the full message may contain connection details.
        print(f"\nSeeding FAILED ({type(exc).__name__}). Nothing was saved.")
        print("Check that PostgreSQL is running and 'alembic upgrade head' has been run.")
        raise SystemExit(1)
    finally:
        db.close()

    print(f"\nDone. Created {users_created} user(s) and {tasks_created} task(s).")
    print("LOCAL TESTING ONLY: admin@example.com / Admin@12345 and user@example.com / User@12345")


if __name__ == "__main__":
    seed()