# Task Manager — Full Stack (FastAPI + React)

RESTful task management system: users can create, read, update and delete tasks, assign them to
users, mark them as completed and filter them by status and due date.

## Tech stack

| Layer            | Choice                                              |
| ---------------- | --------------------------------------------------- |
| API              | FastAPI (OpenAPI / Swagger at `/docs`)              |
| Persistence      | PostgreSQL 16 + SQLAlchemy 2.0 + Alembic             |
| Auth             | JWT (PyJWT) + bcrypt password hashing                |
| Rate limiting    | slowapi                                              |
| Background jobs  | Celery + Redis                                       |
| Tests            | pytest + pytest-cov (>= 80% coverage enforced)        |
| Tooling          | uv + `pyproject.toml`, ruff, mypy, pre-commit         |
| Frontend         | React + TypeScript + Vite                             |
| Containers       | Docker + docker-compose                               |

## Architecture (Clean Architecture)

```
backend/app/
├── domain/          # Entities and business rules (no framework imports)
├── application/     # Use cases + repository interfaces (ports)
├── infrastructure/  # SQLAlchemy repos, JWT/security, Celery (adapters)
├── api/             # FastAPI routers, request/response schemas, DI
└── core/            # Settings / configuration
```

Dependencies point inwards: `api -> application -> domain`, and `infrastructure` implements the
interfaces defined in `application`.

## Getting started

> Full instructions will be completed as the project evolves.

```bash
cp .env.example .env
docker compose up -d db redis

cd backend
uv sync
uv run pytest
uv run uvicorn app.main:app --reload
```

## GenAI

See [GENAI.md](GENAI.md).
