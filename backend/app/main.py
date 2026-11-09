from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Task Manager API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
