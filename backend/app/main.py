from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.analyses import router as analyses_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.recommendations import router as recommendations_router
from app.api.standards import router as standards_router
from app.core.config import settings

app = FastAPI(
    title="SIH26108 Indian Standards Recommendation API",
    version="2.0.0",
    description="Decision-support API. It does not make legal, compliance, or tender decisions.",
)
origins = [
    item.strip()
    for item in (
        settings.cors_origins
        or "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if item.strip()
]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                       allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])
app.include_router(health_router, prefix="/api")
app.include_router(analyses_router, prefix="/api")
app.include_router(standards_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
