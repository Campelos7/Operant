from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from operant.app.models.membership import Membership
from operant.app.models.organization import Organization


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, org_id: UUID) -> Organization | None:
        return self.db.get(Organization, org_id)

    def get_by_slug(self, slug: str) -> Organization | None:
        stmt = select(Organization).where(Organization.slug == slug)
        return self.db.execute(stmt).scalars().first()

    def list_for_user(self, user_id: UUID, *, limit: int, offset: int) -> tuple[list[Organization], int]:
        base = (
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(Membership.user_id == user_id)
        )
        total = int(self.db.execute(select(func.count()).select_from(base.subquery())).scalar_one())
        stmt = base.order_by(Organization.created_at.desc()).limit(limit).offset(offset)
        items = self.db.execute(stmt).scalars().all()
        return items, total

    def create(self, *, name: str, slug: str) -> Organization:
        org = Organization(name=name, slug=slug)
        self.db.add(org)
        self.db.flush()
        return org


