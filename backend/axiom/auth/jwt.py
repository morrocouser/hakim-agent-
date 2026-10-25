"""Authentication — JWT + bcrypt pour APEX."""

import os
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dotenv import load_dotenv
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, delete
from axiom.db.models import User, RevokedToken, get_session
from axiom.logging_setup import log

# Load .env relative to backend directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("HAKIM_JWT_SECRET") or os.getenv("AXIOM_JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError(
        "HAKIM_JWT_SECRET is not set. The server refuses to start with an "
        "insecure default. Generate one with: "
        "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes (reduced from 7 days)
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days for refresh token

security = HTTPBearer(auto_error=False)

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(data: dict, expires_delta: timedelta, token_type: str = TOKEN_TYPE_ACCESS) -> str:
    """
    Create a JWT token with type claim.
    
    Args:
        data: Payload data
        expires_delta: Token expiration time
        token_type: Type of token (access or refresh)
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": token_type,
        "jti": secrets.token_hex(16),  # Unique token ID
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token (15 min expiry)."""
    return create_token(
        data,
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        TOKEN_TYPE_ACCESS
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create refresh token (7 days expiry)."""
    return create_token(
        data,
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        TOKEN_TYPE_REFRESH
    )


def decode_token(token: str, expected_type: Optional[str] = None) -> Optional[dict]:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string
        expected_type: si fourni, le claim `type` doit correspondre exactement
            (un refresh token ne doit jamais être accepté comme access token).

    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_type": False}  # We check type manually
        )

        token_type = payload.get("type")
        if token_type not in [TOKEN_TYPE_ACCESS, TOKEN_TYPE_REFRESH]:
            log.warning(f"Type de token invalide: {token_type}")
            return None
        if expected_type and token_type != expected_type:
            log.warning(f"Type de token inattendu: {token_type} (attendu {expected_type})")
            return None

        return payload
    except JWTError as e:
        log.warning(f"Décodage token échoué: {e}")
        return None


async def is_token_revoked(session, jti: Optional[str]) -> bool:
    """Vrai si le jti est absent (jeton non révocable) ou présent dans la liste de révocation."""
    if not jti:
        return True
    result = await session.execute(select(RevokedToken.jti).where(RevokedToken.jti == jti))
    return result.scalar_one_or_none() is not None


async def revoke_token(session, payload: dict) -> None:
    """Révoque le jti d'un payload décodé (idempotent) et purge les entrées expirées."""
    jti = payload.get("jti")
    if not jti:
        return
    exp = payload.get("exp")
    expires_at = datetime.utcfromtimestamp(exp) if exp else datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await session.execute(delete(RevokedToken).where(RevokedToken.expires_at < datetime.utcnow()))
    if not await is_token_revoked(session, jti):
        session.add(RevokedToken(jti=jti, expires_at=expires_at))
    await session.commit()


async def get_current_user(
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Dépendance FastAPI pour récupérer l'utilisateur courant.

    Accepte le token via header `Authorization: Bearer` OU cookie httpOnly
    `access_token` (préférable : non exfiltrable par XSS).
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif request and request.cookies.get("access_token"):
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")

    payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    session = await get_session()
    try:
        if await is_token_revoked(session, payload.get("jti")):
            raise HTTPException(status_code=401, detail="Token révoqué")
        result = await session.execute(select(User).where(User.id == payload["user_id"]))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        return user
    finally:
        await session.close()


async def optional_user(
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[User]:
    """Comme get_current_user mais retourne None si non authentifié."""
    try:
        return await get_current_user(request=request, credentials=credentials)
    except HTTPException:
        return None



def _admin_usernames() -> set[str]:
    raw = os.getenv("HAKIM_ADMIN_USERS", "")
    return {u.strip().lower() for u in raw.split(",") if u.strip()}


def is_admin(user: User) -> bool:
    """Admin = username listé dans HAKIM_ADMIN_USERS (vide => personne, fail-closed)."""
    return user.username.lower() in _admin_usernames()


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dépendance FastAPI : réserve une route aux administrateurs."""
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Droits administrateur requis")
    return user
