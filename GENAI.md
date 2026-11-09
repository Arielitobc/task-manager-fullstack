# How I used GenAI in this project

## The tool

I used **Claude** as my coding assistant. It could run commands, so it was able to run the
tests, the linters and the app itself while we worked.

I didn't ask it to "build the whole app" in one go. I went step by step:

1. Domain and business rules
2. Use cases
3. Database and security
4. API endpoints
5. Docker
6. Frontend

After each step I ran the tests, read the code, and only then moved on. I decided the
architecture, the permission rules and the quality bar (tests first, at least 80% coverage,
strict type checks). The AI wrote most of the first drafts, and I reviewed and fixed them.

---

## The prompts

### Main backend prompt

This is the prompt I used to generate the backend scaffold:

```text
You are a senior Python backend engineer. Build the backend of a task management REST API.

Stack (mandatory):
- FastAPI, SQLAlchemy 2.0 (typed Mapped[] models), Alembic, PostgreSQL (SQLite for tests)
- JWT auth with PyJWT (OAuth2 password flow so Swagger "Authorize" works), bcrypt hashing
- slowapi rate limiting, Celery + Redis for background jobs
- uv + pyproject.toml, ruff, mypy --strict, pytest + pytest-cov (fail under 80%)

Architecture (Clean Architecture, strictly enforced):
- app/domain: dataclass entities (User, Task, TaskStatus enum) and business rules.
  NO imports from FastAPI, SQLAlchemy or Pydantic.
- app/application: repository/service ports as typing.Protocol + use case classes
  (AuthService, TaskService) that depend only on ports.
- app/infrastructure: SQLAlchemy models + repositories that map ORM <-> domain entities
  (ORM objects must never leave this layer), JWT/bcrypt adapters, Celery app.
- app/api: routers, Pydantic schemas, dependency wiring, domain-error -> HTTP mapping.

Business rules:
- A task has title (1-200 chars, trimmed), description, status (pending|in_progress|completed),
  due_date (date, optional), owner_id, assignee_id (optional), completed_at.
- Owner can update/delete. Assignee can view and complete. Anyone else gets 404 (not 403).
- Completing sets completed_at; moving away from completed clears it. Completing is idempotent.
- Assigning to someone else enqueues a Celery notification; so does an assignee completing.
- PATCH must distinguish "field omitted" from "field: null" (null due_date clears it).

Endpoints under /api/v1: auth (register, login, me), users (list active), tasks
(list with pagination page/size<=100 and filters status, due_date_from, due_date_to,
assignee_id, search; create; get; patch; delete; POST /{id}/assign; POST /{id}/complete).

Testing (TDD): write the tests first.
- Unit tests for entities and use cases with in-memory fake repositories (no DB).
- API tests with TestClient + in-memory SQLite, covering auth errors, permissions,
  validation, pagination and every filter.

Do not invent library APIs. If unsure about a version-specific behaviour, say so.
Output the file tree first, then each file.
```

A few things I made sure were in this prompt:

- **The exact stack.** If you don't say it, the AI picks whatever it likes.
- **The layer rules.** For example, "no FastAPI or SQLAlchemy in the domain". Without this, the
  AI tends to mix everything together.
- **The business rules spelled out.** Who can edit, who can complete, what happens with `null`.
  The AI can't guess these.
- **"Write the tests first".** That way I had something to check the code against.
- **"Do not invent library APIs".** It cuts down on made-up functions.

### Frontend prompt

```text
Build the frontend for the task API above with React 19 + TypeScript + Vite.

- React Router 7 (no v6 future-flag console warnings), TanStack Query for server state.
- Folders: api/ (typed fetch client + endpoints), auth/ (context + protected routes),
  hooks/ (query hooks, URL-synced filters), components/ (presentational), pages/ (containers).
- Login (with a "use demo account" button), register, and a tasks page: responsive card grid,
  filters (search debounced, status, due date range) stored in the URL, pagination with page
  size, a create/edit modal, delete confirmation, complete button.
- Show Edit/Delete only to the owner and Complete to owner/assignee (mirror the API rules).
- Turn FastAPI error payloads (string or 422 array) into readable messages; logout on 401.
- No UI library: plain CSS with variables, mobile-first, dark mode. Accessible forms and modal.
- Tests with Vitest + Testing Library, mocking fetch: login flow, CRUD flow, filters sent to
  the API, form validation, permission-based buttons.
- Requirement: zero warnings in the browser console.
```

### Follow-up prompts

Most of the useful work came from short follow-ups after I found a problem:

```text
Write a test that turns the rate limiter ON and does a SUCCESSFUL login.
Right now the tests only try failed logins, with the limiter turned off.
```

```text
With Redis stopped, assigning a task takes 19 seconds. Find out where it's
blocking and make it fail fast without breaking the request.
```

```text
Run the migration up, down and up again on a real PostgreSQL and fix whatever breaks.
```

---

## Some of the code it generated

This is one of the use cases. I kept it almost as it came out, because it was clean. It has
no web or database code, only business rules:

```python
@dataclass
class TaskService:
    tasks: TaskRepository
    users: UserRepository
    notifier: NotificationDispatcher

    def get_task(self, actor: User, task_id: int) -> Task:
        task = self.tasks.get_by_id(task_id)
        # Return 404 (not 403) so we don't reveal that the task exists.
        if not task or not task.is_visible_to(self._id(actor)):
            raise NotFoundError(f"Task {task_id} not found")
        return task

    def complete_task(self, actor: User, task_id: int) -> Task:
        task = self.get_task(actor, task_id)          # owner OR assignee
        if task.status is TaskStatus.COMPLETED:
            return task                                # calling it twice is fine
        task.complete()
        updated = self.tasks.update(task)
        if updated.owner_id != self._id(actor):
            self.notifier.task_completed(self._id_of(updated), updated.owner_id)
        return updated
```

And the database query for the task list, with filters and pagination:

```python
query = select(TaskModel).where(
    or_(TaskModel.owner_id == user_id, TaskModel.assignee_id == user_id)
)
if f.status is not None:
    query = query.where(TaskModel.status == f.status)
if f.due_date_from is not None:
    query = query.where(TaskModel.due_date >= f.due_date_from)
...
rows = session.scalars(
    query.order_by(TaskModel.due_date.asc().nulls_last(), TaskModel.id.desc())
    .offset(page.offset).limit(page.size)
)
```

---

## How I checked what the AI wrote

I don't trust AI code just because it looks good, so I checked it in five ways:

1. **Tests.** 59 backend tests and 24 frontend tests. The backend fails the build if coverage
   drops below 80% (it's at 99%).
2. **Linters and type checks** (`ruff`, `mypy --strict`, ESLint, TypeScript). When the AI uses
   a function that doesn't exist, the type checker usually catches it.
3. **Running the real thing, not just mocks.** I ran the API against a real PostgreSQL, Redis
   and Celery worker and tested it by hand. This is where I found the worst bugs (see below).
4. **Running the migration both ways** (up, down, up again) on PostgreSQL.
5. **Reading the code with security in mind.**
   - Does the API ever return the password?
   - Can someone find out which emails are registered?
   - Is every endpoint protected?
   - Are the JWT checks strict?

---

## What I had to fix

All the tests were green and the code looked fine, but these problems were still there:

| # | Problem | How I found it | Fix |
|---|---|---|---|
| 1 | **A successful login returned a 500 error.** The rate limiting library needs an extra `response` parameter on the endpoint. | Testing by hand with `curl`. The tests passed because they run with the rate limiter turned off. | Added the parameter, and a new test that turns the limiter on and does a successful login. |
| 2 | **Requests took 19 seconds when Redis was down.** Celery kept retrying the connection while the user waited. | I stopped Redis on purpose and timed the request. | Celery doesn't need to store results here, so I removed that and made it give up quickly. Now it takes 2 seconds and the request still works. |
| 3 | **The migration couldn't be undone and re-applied.** It left a PostgreSQL ENUM type behind. | Running the migration down and up again. | Drop the ENUM type explicitly in `downgrade()`. |
| 4 | It suggested **`passlib`** for passwords. | I know this library is no longer maintained and breaks with newer `bcrypt`. | Used `bcrypt` directly. |
| 5 | A setting in `.env.example` was in the **wrong format** (`CORS_ORIGINS`). The app would crash on start. | Reading the config code. | Changed it to the JSON list format the app expects. |
| 6 | **Dates showed one day off** in the frontend. `new Date('2026-03-01')` is read as UTC, and Bolivia is UTC-4, so it shows Feb 28. | Code review. This is a common bug. | Parse dates as local dates. Added a test. |
| 7 | A frontend test **passed or failed by luck**. It searched for the text "Completed", which also appears in the filter dropdown. | Running the tests. | Test what the user actually sees change instead of searching for text. |
| 8 | Small things: a deprecated constant, a wrong type hint, and database connections not being closed in tests. | Warnings and the type checker. | Fixed each one. |

**My main takeaway:** green tests from AI code aren't enough. The two worst bugs (#1 and #2)
only showed up when I ran the app for real and tried things going wrong on purpose.

---

## Edge cases, login and validation

**Login and security**
- Logins use JWT tokens that expire after 60 minutes.
- Tokens that are fake, expired or signed with another key are rejected (401).
- Wrong email and wrong password give the **same** error message, so nobody can find out which
  emails exist.
- Login and register allow 5 tries per minute per IP, and the rest of the API 100 per minute,
  to stop brute force.
- Passwords are hashed with bcrypt and never returned by the API.

**Permissions**
- The owner can edit and delete a task.
- The assignee can see it and mark it as completed, but can't edit or delete it (403).
- Anyone else gets a 404, as if the task didn't exist.

**Validation**
- Empty titles, or titles over 200 characters, are rejected.
- The email format is checked.
- Page size can't be more than 100.
- You can't assign a task to a user who doesn't exist.
- The "due from" date can't be after the "due to" date.
- When editing, leaving a field out keeps its value. Sending `due_date: null` clears the date.

---

## Is the code fast and well written?

- **Database:** listing tasks is always two queries (one to count, one for the page), never one
  per task. I added indexes for the columns we filter on.
- **Python style:** dataclasses and enums for the business objects, typed SQLAlchemy 2.0 models,
  FastAPI dependencies, and `mypy --strict` with zero errors.
- **Frontend:** small bundle (~100 KB gzipped), no UI library, and **zero warnings in the
  browser console**. I checked this with an automated browser test on desktop and mobile.

**What I never accept from AI without checking:**
- Security settings
- Anything that can make a request slow or hang
- Database migrations
