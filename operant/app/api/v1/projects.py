from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from operant.app.api.deps import db_session, get_org_id, require_min_org_role
from operant.app.core.permissions import OrgRole
from operant.app.schemas.common import Page
from operant.app.schemas.projects import ProjectCreate, ProjectOut, ProjectUpdate
from operant.app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=Page[ProjectOut])
def list_projects(
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.MEMBER)),
    q: str | None = Query(default=None),
    sort: str = Query(default="created_at", pattern=r"^(created_at|name)$"),
    order: str = Query(default="desc", pattern=r"^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = ProjectService(db).list_projects(
        organization_id=org_id, q=q, sort=sort, order=order, limit=limit, offset=offset
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.ADMIN)),
):
    project = ProjectService(db).create_project(
        organization_id=org_id, name=payload.name, description=payload.description
    )
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: UUID,
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.MEMBER)),
):
    return ProjectService(db).get_project_for_org(project_id=project_id, organization_id=org_id)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.ADMIN)),
):
    ProjectService(db).get_project_for_org(project_id=project_id, organization_id=org_id)
    updated = ProjectService(db).update_project(
        project_id=project_id, name=payload.name, description=payload.description
    )
    return updated


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.ADMIN)),
):
    ProjectService(db).get_project_for_org(project_id=project_id, organization_id=org_id)
    ProjectService(db).delete_project(project_id=project_id)
    return None


