from __future__ import annotations

from enum import StrEnum

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from operant.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Plan(StrEnum):
    FREE = "FREE"
    PRO = "PRO"


PLAN_LIMITS: dict[Plan, dict[str, int]] = {
    Plan.FREE: {"max_users": 3, "max_projects": 5},
    Plan.PRO: {"max_users": 50, "max_projects": 100},
}


class Subscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("organization_id", name="uq_subscriptions_org"),)

    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    plan: Mapped[str] = mapped_column(String(20), default=Plan.FREE.value, nullable=False)

    organization = relationship("Organization", back_populates="subscription")


