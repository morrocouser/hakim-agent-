"""Auth Routes — Login, Register, Profile, Refresh Tokens."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from datetime import datetime
from axiom.db.models import User, get_session
from axiom.auth.jwt import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user,
    is_token_revoked, revoke_token,
    TOKEN_TYPE_ACCESS, TOKEN_TYPE_REFRESH,
)
from axiom.logging_setup import log

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    secure: bool = False,
) -> None:
    """Pose des cookies httpOnly (XSS-safe) pour l'access + refresh token.

    Le token reste aussi renvoyé en JSON pour rétro-compatibilité avec les
    clients qui ne gèrent pas les cookies, mais le stockage navigateur en
    localStorage est déconseillé (exfiltrable via XSS).
    """
    secure_cookie = secure or (
        os.getenv("HAKIM_ENV", "development").lower() == "production"
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=15 * 60,  # 15 min (aligné sur ACCESS_TOKEN_EXPIRE_MINUTES)
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 jours
        path="/auth",
    )


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: str = Field(None)
    display_name: str = Field(None)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict
    token_type: str = "bearer"


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str = None
    display_name: str = None
    created_at: str


class LogoutResponse(BaseModel):
    message: str = "Déconnexion réussie"


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, response: Response):
    session = await get_session()
    try:
        # Check if username exists
        existing = await session.execute(select(User).where(User.username == req.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")

        # Create user
        user = User(
            username=req.username,
            email=req.email,
            display_name=req.display_name or req.username,
            password_hash=hash_password(req.password),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        access_token = create_access_token({"user_id": user.id, "username": user.username})
        refresh_token = create_refresh_token({"user_id": user.id})
        # Cookie httpOnly (XSS-safe) en plus du JSON (rétro-compatible)
        _set_auth_cookies(response, access_token, refresh_token)
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={"id": user.id, "username": user.username, "display_name": user.display_name},
        )
    finally:
        await session.close()


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, response: Response):
    session = await get_session()
    try:
        result = await session.execute(select(User).where(User.username == req.username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Identifiants incorrects")

        # Update last login
        user.last_login = datetime.utcnow()
        await session.commit()

        access_token = create_access_token({"user_id": user.id, "username": user.username})
        refresh_token = create_refresh_token({"user_id": user.id})
        _set_auth_cookies(response, access_token, refresh_token)
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={"id": user.id, "username": user.username, "display_name": user.display_name},
        )
    finally:
        await session.close()


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "created_at": str(user.created_at),
    }


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Refresh token valide (sinon cookie httpOnly)")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(response: Response, request: Request, req: Optional[RefreshTokenRequest] = None):
    """
    Rafraîchir l'access token avec un refresh token valide.

    Rotation : le refresh token présenté est révoqué ; le rejouer renvoie 401.
    """
    raw = (req.refresh_token if req else None) or request.cookies.get("refresh_token")
    payload = decode_token(raw, expected_type=TOKEN_TYPE_REFRESH) if raw else None

    if not payload:
        log.warning("Refresh token invalide ou expiré")
        raise HTTPException(status_code=401, detail="Refresh token invalide")

    session = await get_session()
    try:
        if await is_token_revoked(session, payload.get("jti")):
            log.warning("Refresh token révoqué/rejoué")
            raise HTTPException(status_code=401, detail="Refresh token invalide")

        user_id = payload.get("user_id")
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")

        await revoke_token(session, payload)

        access_token = create_access_token({"user_id": user.id, "username": user.username})
        new_refresh = create_refresh_token({"user_id": user.id})
        _set_auth_cookies(response, access_token, new_refresh)

        return RefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh,
        )
    finally:
        await session.close()


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request, response: Response):
    """Déconnexion — révoque les jetons présentés et efface les cookies httpOnly."""
    candidates = [request.cookies.get("access_token"), request.cookies.get("refresh_token")]
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        candidates.append(auth[7:])
    session = await get_session()
    try:
        for raw in candidates:
            payload = decode_token(raw) if raw else None
            if payload:
                await revoke_token(session, payload)
    finally:
        await session.close()
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/auth")
    log.info("Déconnexion demandée")
    return LogoutResponse(message="Déconnexion réussie.")
