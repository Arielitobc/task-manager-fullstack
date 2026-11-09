"""Idempotent demo data. Run with: python -m app.infrastructure.seed"""

from datetime import date, timedelta

from app.core.config import get_settings
from app.domain.entities import Task, TaskStatus, User
from app.infrastructure.persistence.database import build_engine, build_session_factory
from app.infrastructure.persistence.repositories import (
    SqlAlchemyTaskRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.security import BcryptPasswordHasher

DEMO_PASSWORD = "Demo1234!"
DEMO_USERS = [
    ("admin@demo.com", "Ada Admin"),
    ("john@demo.com", "John Doe"),
    ("jane@demo.com", "Jane Smith"),
]


def seed() -> None:
    settings = get_settings()
    factory = build_session_factory(build_engine(settings.database_url))
    hasher = BcryptPasswordHasher()
    with factory() as session, session.begin():
        users_repo = SqlAlchemyUserRepository(session)
        if users_repo.get_by_email(DEMO_USERS[0][0]):
            print("Seed data already present, skipping.")
            return
        users = [
            users_repo.add(User(email=e, full_name=n, hashed_password=hasher.hash(DEMO_PASSWORD)))
            for e, n in DEMO_USERS
        ]
        admin, john, jane = (u.id for u in users)
        assert admin and john and jane
        today = date.today()
        tasks_repo = SqlAlchemyTaskRepository(session)
        samples = [
            (
                "Set up CI pipeline",
                "GitHub Actions with lint + tests",
                admin,
                john,
                2,
                TaskStatus.IN_PROGRESS,
            ),
            (
                "Write API documentation",
                "Review Swagger descriptions",
                admin,
                jane,
                5,
                TaskStatus.PENDING,
            ),
            (
                "Fix login bug",
                "Users with uppercase emails cannot log in",
                john,
                admin,
                -1,
                TaskStatus.PENDING,
            ),
            ("Plan sprint 12", "", admin, None, 7, TaskStatus.PENDING),
            ("Upgrade PostgreSQL", "Move from 15 to 16", jane, admin, 10, TaskStatus.PENDING),
            (
                "Design onboarding flow",
                "Wireframes for new users",
                admin,
                jane,
                3,
                TaskStatus.COMPLETED,
            ),
            (
                "Refactor task service",
                "Extract notification logic",
                admin,
                john,
                1,
                TaskStatus.PENDING,
            ),
            (
                "Security review",
                "Check JWT expiration and rate limits",
                admin,
                None,
                14,
                TaskStatus.PENDING,
            ),
            (
                "Prepare demo",
                "Seeded data and credentials",
                admin,
                admin,
                0,
                TaskStatus.IN_PROGRESS,
            ),
            ("Update dependencies", "", admin, None, None, TaskStatus.COMPLETED),
            (
                "Customer feedback triage",
                "Label and prioritise new issues",
                jane,
                john,
                4,
                TaskStatus.PENDING,
            ),
            (
                "Database backups",
                "Verify nightly backups restore correctly",
                admin,
                jane,
                -3,
                TaskStatus.COMPLETED,
            ),
        ]
        for title, desc, owner, assignee, days, status in samples:
            task = Task(
                title=title,
                description=desc,
                owner_id=owner,
                assignee_id=assignee,
                due_date=today + timedelta(days=days) if days is not None else None,
            )
            if status is not TaskStatus.PENDING:
                task.change_status(status)
            tasks_repo.add(task)
    print(f"Seeded {len(DEMO_USERS)} users and {len(samples)} tasks. Password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
