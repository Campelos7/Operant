from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from operant.app.api.deps import (
    db_session,
    get_current_user,
    get_org_id,
    require_min_org_role,
)
from operant.app.core.permissions import OrgRole
from operant.app.schemas.common import Page
from operant.app.schemas.organizations import (
    AddMemberRequest,
    ChangePlanRequest,
    MemberOut,
    OrganizationCreate,
    OrganizationOut,
    SubscriptionOut,
)
from operant.app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_org(payload: OrganizationCreate, db: Session = Depends(db_session), user=Depends(get_current_user)):
    org = OrganizationService(db).create_org(
        creator_user_id=user.id,
        name=payload.name,
        slug=payload.slug,
    )
    return org


@router.get("", response_model=Page[OrganizationOut])
def list_orgs(
    db: Session = Depends(db_session),
    user=Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = OrganizationService(db).list_orgs_for_user(user_id=user.id, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/current", response_model=OrganizationOut)
def get_current_org(
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _user=Depends(get_current_user),
):
    org = OrganizationService(db).get_org(org_id=org_id)
    return org


@router.get("/members", response_model=Page[MemberOut])
def list_members(
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.ADMIN)),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = OrganizationService(db).list_members(
        organization_id=org_id,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    payload: AddMemberRequest,
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.ADMIN)),
):
    membership = OrganizationService(db).add_member(
        organization_id=org_id, email=payload.email, role=payload.role
    )
    return membership


@router.patch("/subscription", response_model=SubscriptionOut)
def change_plan(
    payload: ChangePlanRequest,
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.OWNER)),
):
    sub = OrganizationService(db).change_plan(organization_id=org_id, plan=payload.plan)
    return SubscriptionOut(organization_id=sub.organization_id, plan=sub.plan)


