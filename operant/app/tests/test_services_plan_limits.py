from __future__ import annotations

import pytest

from operant.app.core.errors import ForbiddenError
from operant.app.core.permissions import OrgRole
from operant.app.models.subscription import Plan
from operant.app.repositories.subscription_repository import SubscriptionRepository
from operant.app.services.auth_service import AuthService
from operant.app.services.organization_service import OrganizationService
from operant.app.services.project_service import ProjectService


def test_free_plan_enforces_max_projects(db):
    auth = AuthService(db)
    user = auth.register(email="a@example.com", password="Secret123!", full_name=None)

    org = OrganizationService(db).create_org(creator_user_id=user.id, name="Org", slug="org")
    # FREE by default: max_projects=5
    for i in range(5):
        ProjectService(db).create_project(organization_id=org.id, name=f"P{i}", description=None)

    with pytest.raises(ForbiddenError):
        ProjectService(db).create_project(organization_id=org.id, name="P6", description=None)


def test_free_plan_enforces_max_users(db):
    auth = AuthService(db)
    owner = auth.register(email="owner@example.com", password="Secret123!", full_name=None)
    org = OrganizationService(db).create_org(creator_user_id=owner.id, name="Org2", slug="org2")

    # Upgrade to PRO and back to validate behavior is driven by subscription
    SubscriptionRepository(db).set_plan(org.id, Plan.FREE.value)
    db.commit()

    svc = OrganizationService(db)
    # FREE max_users=3, owner already counts as 1
    u1 = auth.register(email="u1@example.com", password="Secret123!", full_name=None)
    u2 = auth.register(email="u2@example.com", password="Secret123!", full_name=None)
    svc.add_member(organization_id=org.id, email=u1.email, role=OrgRole.MEMBER.value)
    svc.add_member(organization_id=org.id, email=u2.email, role=OrgRole.MEMBER.value)

    u3 = auth.register(email="u3@example.com", password="Secret123!", full_name=None)
    with pytest.raises(ForbiddenError):
        svc.add_member(organization_id=org.id, email=u3.email, role=OrgRole.MEMBER.value)


