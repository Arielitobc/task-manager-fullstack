from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.errors import register_error_handlers
from app.api.routers import auth, tasks, users
from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.infrastructure.persistence.database import build_engine, build_session_factory

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="Task Manager API",
        version="1.0.0",
        description="Task management REST API: JWT auth, pagination, filtering, rate limiting.",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    engine = build_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)
    app.state.limiter = limiter

    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    register_error_handlers(app)

    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(users.router, prefix=API_PREFIX)
    app.include_router(tasks.router, prefix=API_PREFIX)

    @app.get("/health", tags=["health"])
    @limiter.exempt
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
