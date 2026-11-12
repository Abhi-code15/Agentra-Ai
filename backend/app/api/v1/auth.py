"""Authentication and user session API endpoints."""
from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[UserResponse])
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> SuccessResponse[UserResponse]:
    """Registers a new user account with Argon2id password hashing."""
    service = AuthService(db)
    user = service.register_user(payload)
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.post("/login", response_model=SuccessResponse[TokenResponse])
def login(
    payload: UserLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> SuccessResponse[TokenResponse]:
    """Authenticates credentials, sets rotating HttpOnly refresh cookie, and returns access token."""
    user_agent = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None

    service = AuthService(db)
    user, access_token, refresh_token = service.authenticate_user(
        payload=payload,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    # Set rotating refresh token in HttpOnly, Secure, SameSite=Lax cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    token_data = TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )
    return SuccessResponse(data=token_data)


@router.post("/refresh", response_model=SuccessResponse[RefreshTokenResponse])
def refresh_session(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> SuccessResponse[RefreshTokenResponse]:
    """Rotates refresh token from HttpOnly cookie and returns a fresh access token."""
    if not refresh_token:
        # Fallback to checking Authorization or body if needed, but cookie is primary
        from app.core.exceptions import UnauthorizedException
        raise UnauthorizedException(
            code="AUTH_REFRESH_TOKEN_MISSING",
            message="Refresh token cookie was not provided.",
        )

    user_agent = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None

    service = AuthService(db)
    new_access_token, new_refresh_token = service.rotate_refresh_token(
        raw_refresh_token=refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    # Set rotated cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    refresh_data = RefreshTokenResponse(
        access_token=new_access_token,
        token_type="Bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return SuccessResponse(data=refresh_data)


@router.post("/logout", response_model=SuccessResponse[dict])
def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> SuccessResponse[dict]:
    """Revokes active refresh session and clears the refresh cookie."""
    if refresh_token:
        service = AuthService(db)
        service.logout_user(refresh_token)

    # Clear cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )
    return SuccessResponse(data={"message": "Successfully logged out."})


@router.get("/me", response_model=SuccessResponse[UserResponse])
def get_me(current_user: User = Depends(get_current_user)) -> SuccessResponse[UserResponse]:
    """Returns profile and role of authenticated user."""
    return SuccessResponse(data=UserResponse.model_validate(current_user))
