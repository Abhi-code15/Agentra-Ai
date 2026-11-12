"""API v1 Router aggregation."""
from fastapi import APIRouter
from app.api.v1.analyses import router as analyses_router
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.findings import router as findings_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(analyses_router)
api_v1_router.include_router(findings_router)
