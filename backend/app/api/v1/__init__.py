"""API v1 Router aggregation."""
from fastapi import APIRouter
from app.api.v1.analyses import router as analyses_router
from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.api.v1.findings import router as findings_router
from app.api.v1.reviews import router as reviews_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(analyses_router)
api_v1_router.include_router(findings_router)
api_v1_router.include_router(reviews_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(chat_router)
