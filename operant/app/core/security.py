from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import bcrypt as bcrypt_lib
from jose import JWTError, jwt

from operant.app.core.config import settings


def hash_password(password: str) -> str:
    # Bcrypt has a 72-byte limit. Truncate the password if it exceeds this.
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt_lib.gensalt(rounds=12)
    password_hash = bcrypt_lib.hashpw(password_bytes, salt)
    return password_hash.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    # Apply the same truncation as in hash_password for consistency
    password_bytes = password.encode('utf-8')[:72]
    password_hash_bytes = password_hash.encode('utf-8')
    return bcrypt_lib.checkpw(password_bytes, password_hash_bytes)


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def generate_token_fingerprint() -> str:
    """
    Stable per-token secret used to bind a refresh token record to a concrete token string.
    It's stored only as a hash (no raw token persistence).
    """
    return secrets.token_urlsafe(32)


def hash_refresh_fingerprint(fingerprint: str) -> str:
    # Not a password hash; just a one-way binding to prevent raw storage.
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _encode(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def create_access_token(*, user_id: UUID) -> str:
    jti = str(uuid4())
    exp = now_utc() + timedelta(seconds=settings.jwt_access_ttl_seconds)
    payload = {"sub": str(user_id), "type": "access", "jti": jti, "exp": exp}
    return _encode(payload)


def create_refresh_token(*, user_id: UUID, refresh_jti: UUID, fingerprint: str) -> str:
    """
    Refresh token contains:
    - sub: user id
    - jti: refresh token id (UUID)
    - fp: fingerprint (random secret; stored server-side only as hash)
    """
    exp = now_utc() + timedelta(seconds=settings.jwt_refresh_ttl_seconds)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(refresh_jti),
        "fp": fingerprint,
        "exp": exp,
    }
    return _encode(payload)


class InvalidTokenError(Exception):
    pass


def decode_access_token(token: str) -> tuple[UUID, str]:
    try:
        payload = _decode(token)
    except JWTError as e:
        raise InvalidTokenError("Token inválido") from e
    if payload.get("type") != "access":
        raise InvalidTokenError("Tipo de token inválido")
    return UUID(payload["sub"]), str(payload["jti"])


def decode_refresh_token(token: str) -> tuple[UUID, UUID, str]:
    try:
        payload = _decode(token)
    except JWTError as e:
        raise InvalidTokenError("Token inválido") from e
    if payload.get("type") != "refresh":
        raise InvalidTokenError("Tipo de token inválido")
    return UUID(payload["sub"]), UUID(payload["jti"]), str(payload["fp"])


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


