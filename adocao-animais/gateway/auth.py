
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from dotenv import load_dotenv

load_dotenv()

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def authenticate_user(username: str, password: str) -> bool:
    expected_username = os.getenv("DEMO_USERNAME", "")
    expected_hash = os.getenv("DEMO_PASSWORD_HASH", "")

    if not expected_username or not expected_hash:
        return False

    if username != expected_username:
        return False

    try:
        return password_hash.verify(password, expected_hash)
    except Exception:
        return False


def create_access_token(username: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Token de autenticação obrigatório.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        if not payload.get("sub"):
            raise jwt.InvalidTokenError("Token sem usuário.")

        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
