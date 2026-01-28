from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from operant.app.models.membership import Membership


class MembershipRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_org(self, user_id: UUID, organization_id: UUID) -> Membership | None:
        stmt = select(Membership).where(
            Membership.user_id == user_id, Membership.organization_id == organization_id
        )
        return self.db.execute(stmt).scalars().first()

    def count_users(self, organization_id: UUID) -> int:
        stmt = select(func.count()).select_from(Membership).where(Membership.organization_id == organization_id)
        return int(self.db.execute(stmt).scalar_one())

    def list_members(self, organization_id: UUID, *, limit: int, offset: int) -> tuple[list[Membership], int]:
        base = select(Membership).where(Membership.organization_id == organization_id)
        total = int(self.db.execute(select(func.count()).select_from(base.subquery())).scalar_one())
        stmt = base.order_by(Membership.created_at.desc()).limit(limit).offset(offset)
        items = self.db.execute(stmt).scalars().all()
        return items, total

    def create(self, *, user_id: UUID, organization_id: UUID, role: str) -> Membership:
        membership = Membership(user_id=user_id, organization_id=organization_id, role=role)
        self.db.add(membership)
        self.db.flush()
        return membership


