from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.engine import get_session
from app.models.auth import LoginRequest, LoginResponse, UserInfo
from app.services.auth_service import AuthService
from app.services.user_service import authenticate_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _get_auth_service() -> AuthService:
    return AuthService(
        users_config=settings.users_config,
        jwt_secret=settings.jwt_secret,
        jwt_algorithm=settings.jwt_algorithm,
        jwt_expire_minutes=settings.jwt_expire_minutes,
    )


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供認證 token")
    token = authorization.split(" ", 1)[1]
    service = _get_auth_service()
    user = service.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="無效的 token")
    return user


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    service = _get_auth_service()

    # Try DB auth first
    db_user = await authenticate_db(session, body.email, body.password)
    if db_user:
        user_dict = {
            "email": db_user.email,
            "name": db_user.name,
            "role": db_user.role,
            "monday_user_id": db_user.monday_user_id or "",
        }
        token = service.create_token(user_dict)
        return LoginResponse(access_token=token, user=UserInfo(**user_dict))

    # Fallback to env config (for initial setup before DB is seeded)
    user = service.authenticate(body.email, body.password)
    if user:
        token = service.create_token(user)
        return LoginResponse(access_token=token, user=UserInfo(**user))

    raise HTTPException(status_code=401, detail="帳號或密碼錯誤")


@router.get("/me", response_model=UserInfo)
async def me(current_user: dict = Depends(get_current_user)):
    return UserInfo(
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        monday_user_id=current_user.get("monday_user_id", ""),
    )
