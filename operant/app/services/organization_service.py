from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from operant.app.core.errors import ConflictError, ForbiddenError, NotFoundError
from operant.app.core.permissions import OrgRole
from operant.app.models.subscription import PLAN_LIMITS, Plan
from operant.app.repositories.membership_repository import MembershipRepository
from operant.app.repositories.organization_repository import OrganizationRepository
from operant.app.repositories.subscription_repository import SubscriptionRepository
from operant.app.repositories.user_repository import UserRepository


class OrganizationService:
    def __init__(self, db: Session):
        self.db = db
        self.orgs = OrganizationRepository(db)
        self.memberships = MembershipRepository(db)
        self.subscriptions = SubscriptionRepository(db)
        self.users = UserRepository(db)

    def create_org(self, *, creator_user_id, name: str, slug: str):
        if self.orgs.get_by_slug(slug) is not None:
            raise ConflictError("Slug já está em uso")
        try:
            org = self.orgs.create(name=name, slug=slug)
            self.subscriptions.create(organization_id=org.id, plan=Plan.FREE.value)
            self.memberships.create(
                user_id=creator_user_id, organization_id=org.id, role=OrgRole.OWNER.value
            )
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("Não foi possível criar organização") from e
        return org

    def list_orgs_for_user(self, *, user_id, limit: int, offset: int):
        return self.orgs.list_for_user(user_id, limit=limit, offset=offset)

    def get_org(self, *, org_id):
        org = self.orgs.get(org_id)
        if org is None:
            raise NotFoundError("Organização não encontrada")
        return org

    def list_members(self, *, organization_id, limit: int, offset: int):
        return self.memberships.list_members(organization_id, limit=limit, offset=offset)

    def add_member(self, *, organization_id, email: str, role: str):
        user = self.users.get_by_email(email)
        if user is None:
            raise NotFoundError("Usuário não encontrado")

        if self.memberships.get_by_user_org(user.id, organization_id) is not None:
            raise ConflictError("Usuário já é membro desta organização")

        sub = self.subscriptions.get_by_org(organization_id)
        plan = Plan(sub.plan) if sub else Plan.FREE
        limits = PLAN_LIMITS[plan]
        current = self.memberships.count_users(organization_id)
        if current >= limits["max_users"]:
            raise ForbiddenError("Limite de usuários do plano atingido")

        try:
            membership = self.memberships.create(
                user_id=user.id, organization_id=organization_id, role=role
            )
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("Não foi possível adicionar membro") from e
        return membership

    def change_plan(self, *, organization_id, plan: str):
        if plan not in (Plan.FREE.value, Plan.PRO.value):
            raise ConflictError("Plano inválido")
        sub = self.subscriptions.set_plan(organization_id, plan)
        self.db.commit()
        return sub


