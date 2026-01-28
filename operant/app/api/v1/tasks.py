from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from operant.app.api.deps import db_session, get_org_id, require_min_org_role
from operant.app.core.permissions import OrgRole
from operant.app.schemas.common import Page
from operant.app.schemas.tasks import TaskCreate, TaskOut, TaskUpdate
from operant.app.services.project_service import ProjectService
from operant.app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _ensure_project_in_org(db: Session, *, project_id: UUID, org_id: UUID):
    return ProjectService(db).get_project_for_org(project_id=project_id, organization_id=org_id)


@router.get("", response_model=Page[TaskOut])
def list_tasks(
    project_id: UUID = Query(...),
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.MEMBER)),
    status_filter: str | None = Query(default=None, alias="status", pattern=r"^(TODO|IN_PROGRESS|DONE)$"),
    sort: str = Query(default="created_at", pattern=r"^(created_at|title)$"),
    order: str = Query(default="desc", pattern=r"^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    _ensure_project_in_org(db, project_id=project_id, org_id=org_id)
    items, total = TaskService(db).list_tasks(
        project_id=project_id,
        status=status_filter,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    project_id: UUID = Query(...),
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.MEMBER)),
):
    _ensure_project_in_org(db, project_id=project_id, org_id=org_id)
    task = TaskService(db).create_task(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
    )
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: UUID,
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.MEMBER)),
):
    task = TaskService(db).get_task(task_id=task_id)
    _ensure_project_in_org(db, project_id=task.project_id, org_id=org_id)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.MEMBER)),
):
    task = TaskService(db).get_task(task_id=task_id)
    _ensure_project_in_org(db, project_id=task.project_id, org_id=org_id)
    updated = TaskService(db).update_task(
        task_id=task_id, title=payload.title, description=payload.description, status=payload.status
    )
    return updated


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    _membership=Depends(require_min_org_role(OrgRole.ADMIN)),
):
    task = TaskService(db).get_task(task_id=task_id)
    _ensure_project_in_org(db, project_id=task.project_id, org_id=org_id)
    TaskService(db).delete_task(task_id=task_id)
    return None


