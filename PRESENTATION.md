# Task Manager: Presentation and Thought Process

## 1. The user story

> **As a** member of a small team,
> **I want to** create tasks, assign them to my teammates and see what's pending or overdue,
> **so that** everyone knows what they have to do and when.

**What a user can do:**
- Sign up, log in and log out.
- Create, view, edit and delete their tasks.
- Assign a task to a teammate. The teammate gets a notification (background job).
- Mark a task as completed. The owner gets notified if someone else completes it.
- Filter tasks by status, by due date range and by text, with pagination.

**Rules I defined:**

| Who | Can see | Can edit / delete | Can complete |
|---|---|---|---|
| Owner (created it) | ✅ | ✅ | ✅ |
| Assignee | ✅ | ❌ (403) | ✅ |
| Anyone else | ❌ (404) | ❌ | ❌ |

I return 404 (not 403) to strangers so the API doesn't reveal that the task exists.

---

## 2. How I approached it

1. **Read the requirements and made a checklist.** Every requirement in the PDF maps to
   something in the repo (see section 6).
2. **Picked the stack.** FastAPI (Swagger comes built in), PostgreSQL, SQLAlchemy 2, Celery +
   Redis, React + TypeScript.
3. **Designed the layers before writing code** (Clean Architecture), so the business rules
   don't depend on FastAPI or the database.
4. **Built from the inside out, tests first:**
   1. Domain rules (Task, User, status) with unit tests.
   2. Use cases (create, assign, complete…) tested with fake in-memory repositories, with no
      database involved.
   3. Database repositories, JWT, bcrypt, Celery.
   4. API endpoints with API tests.
   5. Docker, migrations and seed data.
   6. Frontend.
5. **Tested against real infrastructure** (PostgreSQL, Redis, Celery worker, a real browser),
   not just mocks. This found bugs the unit tests missed (see `GENAI.md`).
6. **Wrote the docs** (README, GENAI.md, this file).

---

## 3. Architecture

```
            ┌──────────────────────────────┐
  React ──▶ │  api/        FastAPI routers │  HTTP, validation (Pydantic), errors → status codes
            ├──────────────────────────────┤
            │  application/  use cases     │  AuthService, TaskService + interfaces (ports)
            ├──────────────────────────────┤
            │  domain/     entities, rules │  Task, User, TaskStatus. Pure Python.
            └──────────────────────────────┘
                          ▲ implements the interfaces
            ┌──────────────────────────────┐
            │ infrastructure/              │  SQLAlchemy + PostgreSQL, JWT, bcrypt,
            │                              │  Celery + Redis, seed data
            └──────────────────────────────┘
```

- **The domain doesn't import anything** from FastAPI or SQLAlchemy.
- **Use cases only know interfaces** ("give me a task repository"). In production that's
  PostgreSQL; in unit tests it's a Python dictionary. This is why 30+ unit tests run in
  milliseconds.
- **One place maps errors to HTTP codes.** Use cases raise `NotFoundError` or
  `PermissionDeniedError`, and the API turns them into 404 or 403.

**Frontend structure:**
- `api/`: a typed fetch client that adds the token and turns API errors into readable messages.
- `auth/`: login state and protected routes.
- `hooks/`: data fetching with TanStack Query, and filters synced with the URL.
- `components/`: small UI pieces (card, form, modal, pagination).
- `pages/`: login, register, tasks.

---

## 4. Key decisions

| Decision | Why |
|---|---|
| FastAPI | Swagger docs for free, validation with Pydantic, clean dependency injection. |
| PostgreSQL + Alembic migrations | A real database with versioned schema changes. SQLite is only used for tests. |
| JWT (OAuth2 password flow) | Stateless, and the Swagger "Authorize" button works out of the box. |
| Same error for wrong email or password | Nobody can find out which emails are registered. |
| Rate limiting: 5/min on login, 100/min elsewhere | Stops brute-force attacks. Stored in Redis so it works with several API processes. |
| Celery + Redis for notifications | Slow work doesn't block the user. If Redis is down, the request still works. |
| PATCH only changes the fields you send | `"due_date": null` clears the date; leaving it out keeps it. |
| Filters live in the URL (frontend) | Links can be shared, refresh keeps the filters, and the back button works. |
| No UI library (plain CSS) | Small bundle, full control, responsive, dark mode. |
| Seed data runs on every start (idempotent) | The demo always has users and tasks ready. |

---

## 5. Quality

- **Backend:** 59 tests, **99% coverage** (the build fails under 80%), `ruff` and `mypy --strict`.
- **Frontend:** 24 tests (Vitest + Testing Library), ~99% coverage, ESLint and TypeScript strict.
- **End-to-end:** a Playwright script logs in, creates, filters, edits, completes and deletes a
  task, and paginates, on desktop and mobile. **0 browser console warnings.**
- **CI:** GitHub Actions runs lint, types and tests on every push.
- **pre-commit:** ruff runs before every commit.

---

## 6. Requirements checklist

| Requirement | Where |
|---|---|
| CRUD tasks, assign, complete | `backend/app/api/routers/tasks.py` |
| Filter by status and due date | `GET /api/v1/tasks?status=&due_date_from=&due_date_to=` |
| FastAPI | `backend/app/main.py` |
| JWT authentication | `backend/app/infrastructure/security.py`, `api/deps.py` |
| Pagination | `page` & `size` params, response has `total` and `pages` |
| PostgreSQL / SQLite + schema | `infrastructure/persistence/models.py`, `migrations/` |
| Unit tests ≥ 80% coverage | `backend/tests/` (99%) |
| Dockerfile + docker-compose | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |
| README with setup + decisions | `README.md` |
| Swagger docs | http://localhost:8000/docs |
| pyproject.toml (uv), pre-commit | `backend/pyproject.toml`, `.pre-commit-config.yaml` |
| Rate limiting | `backend/app/core/rate_limit.py` |
| Background tasks (Celery + Redis) | `backend/app/infrastructure/celery_app.py` |
| Frontend with CRUD, responsive | `frontend/` (React + TypeScript) |
| Seeded data / demo credentials | `admin@demo.com` / `Demo1234!` |
| GenAI answers | `GENAI.md` |

---

## 7. Demo script (about 10 minutes)

1. `docker compose up --build`. Show the 5 containers: db, redis, api, worker, frontend.
2. **Swagger** (http://localhost:8000/docs):
   1. Log in with Authorize.
   2. Call `GET /tasks` with filters.
   3. Show the 401 error you get without a token.
3. **Frontend** (http://localhost:3000):
   1. Click "Use demo account".
   2. Show the task list, the overdue task in red, and the badges.
   3. Create a task assigned to Jane, then show the worker log with the notification.
   4. Filter by status and by dates, and show the URL changing.
   5. Edit, complete and delete a task.
   6. Change the page size and paginate.
   7. Log in as `jane@demo.com`: she can complete the task but has no Edit/Delete buttons.
   8. Open a phone-sized view to show it's responsive.
4. **Rate limit:** try a wrong password 6 times and get a 429.
5. **Code tour:**
   1. `domain/entities.py` (the business rules).
   2. `use_cases/tasks.py`.
   3. A fake repository in the tests.
   4. Run `uv run pytest` to show the coverage.
6. **GenAI:** go through `GENAI.md`, especially the bugs found by testing for real.

---

## 8. What I'd do next

- **Refresh tokens**, and storing the token in an httpOnly cookie instead of localStorage.
- **Transactional outbox** so a notification is only sent if the database transaction commits.
- **Real notifications** (email or websockets) instead of logs.
- **Roles** (admin, member) and teams or projects.
- **Cursor pagination** for very large lists.
