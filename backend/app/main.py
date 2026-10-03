from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, analysis, grievance
from .core.config import settings

app = FastAPI(title="NiveshShakti Backend")

# CORS (allow frontend dev origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(grievance.router, prefix="/grievance", tags=["grievance"])
