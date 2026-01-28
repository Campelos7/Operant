from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from operant.app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, token_id: UUID) -> RefreshToken | None:
        return self.db.get(RefreshToken, token_id)

    def create(
        self,
        *,
        token_id: UUID,
        user_id: UUID,
        fingerprint_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        rt = RefreshToken(id=token_id, user_id=user_id, fingerprint_hash=fingerprint_hash, expires_at=expires_at)
        self.db.add(rt)
        self.db.flush()
        return rt

    def revoke(self, token: RefreshToken, *, revoked_at: datetime, replaced_by: UUID | None) -> RefreshToken:
        token.revoked_at = revoked_at
        token.replaced_by = replaced_by
        self.db.flush()
        return token

    def revoke_all_for_user(self, user_id: UUID, *, revoked_at: datetime) -> int:
        # Conservative: load and update (keeps it simple/portable)
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        tokens = self.db.execute(stmt).scalars().all()
        for t in tokens:
            t.revoked_at = revoked_at
        self.db.flush()
        return len(tokens)


