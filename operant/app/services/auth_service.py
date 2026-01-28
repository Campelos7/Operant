from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from operant.app.core.config import settings
from operant.app.core.errors import ConflictError, UnauthorizedError
from operant.app.core.security import (
    TokenPair,
    constant_time_equals,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_token_fingerprint,
    hash_password,
    hash_refresh_fingerprint,
    now_utc,
    verify_password,
)
from operant.app.repositories.refresh_token_repository import RefreshTokenRepository
from operant.app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def register(self, *, email: str, password: str, full_name: str | None):
        password_hash = hash_password(password)
        try:
            user = self.users.create(email=email, password_hash=password_hash, full_name=full_name)
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("Email já está em uso") from e
        return user

    def login(self, *, email: str, password: str) -> TokenPair:
        user = self.users.get_by_email(email)
        if user is None or not user.is_active:
            raise UnauthorizedError("Credenciais inválidas")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Credenciais inválidas")
        return self._issue_pair(user.id)

    def refresh(self, *, refresh_token: str) -> TokenPair:
        user_id, refresh_jti, fingerprint = decode_refresh_token(refresh_token)
        record = self.refresh_tokens.get(refresh_jti)
        if record is None or record.user_id != user_id:
            raise UnauthorizedError("Refresh token inválido")
        if record.revoked_at is not None:
            raise UnauthorizedError("Refresh token revogado")
        if record.expires_at <= now_utc():
            raise UnauthorizedError("Refresh token expirado")

        fp_hash = hash_refresh_fingerprint(fingerprint)
        if not constant_time_equals(fp_hash, record.fingerprint_hash):
            raise UnauthorizedError("Refresh token inválido")

        new_pair = self._issue_pair(user_id)
        # rotate: revoke old and link to new jti (decoded from new token)
        _, new_refresh_jti, _ = decode_refresh_token(new_pair.refresh_token)
        self.refresh_tokens.revoke(record, revoked_at=now_utc(), replaced_by=new_refresh_jti)
        self.db.commit()
        return new_pair

    def logout(self, *, refresh_token: str) -> None:
        user_id, refresh_jti, fingerprint = decode_refresh_token(refresh_token)
        record = self.refresh_tokens.get(refresh_jti)
        if record is None or record.user_id != user_id:
            # logout is idempotent-ish
            return
        fp_hash = hash_refresh_fingerprint(fingerprint)
        if not constant_time_equals(fp_hash, record.fingerprint_hash):
            return
        if record.revoked_at is None:
            self.refresh_tokens.revoke(record, revoked_at=now_utc(), replaced_by=None)
            self.db.commit()

    def _issue_pair(self, user_id: UUID) -> TokenPair:
        access = create_access_token(user_id=user_id)

        refresh_id = uuid4()
        fingerprint = generate_token_fingerprint()
        refresh = create_refresh_token(user_id=user_id, refresh_jti=refresh_id, fingerprint=fingerprint)

        expires_at = now_utc() + timedelta(seconds=settings.jwt_refresh_ttl_seconds)
        self.refresh_tokens.create(
            token_id=refresh_id,
            user_id=user_id,
            fingerprint_hash=hash_refresh_fingerprint(fingerprint),
            expires_at=expires_at,
        )
        self.db.commit()
        return TokenPair(access_token=access, refresh_token=refresh)


