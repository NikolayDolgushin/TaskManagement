from fastapi import FastAPI

from app.api.routes import auth, users
from app.core.config import settings
from app.modules.projects.router import router as projects_router

app = FastAPI(title=settings.APP_NAME)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "task-management"}
