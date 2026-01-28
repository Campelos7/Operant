from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from operant.app.models.subscription import Subscription


class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_org(self, organization_id: UUID) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.organization_id == organization_id)
        return self.db.execute(stmt).scalars().first()

    def create(self, *, organization_id: UUID, plan: str) -> Subscription:
        sub = Subscription(organization_id=organization_id, plan=plan)
        self.db.add(sub)
        self.db.flush()
        return sub

    def set_plan(self, organization_id: UUID, plan: str) -> Subscription:
        sub = self.get_by_org(organization_id)
        if sub is None:
            sub = self.create(organization_id=organization_id, plan=plan)
        else:
            sub.plan = plan
            self.db.flush()
        return sub


