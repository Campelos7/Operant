from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from operant.app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, project_id: UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def count_for_org(self, organization_id: UUID) -> int:
        stmt = select(func.count()).select_from(Project).where(Project.organization_id == organization_id)
        return int(self.db.execute(stmt).scalar_one())

    def list_for_org(
        self,
        organization_id: UUID,
        *,
        q: str | None,
        sort: str,
        order: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Project], int]:
        stmt = select(Project).where(Project.organization_id == organization_id)
        if q:
            stmt = stmt.where(Project.name.ilike(f"%{q}%"))

        total = int(self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one())

        sort_col = Project.created_at if sort == "created_at" else Project.name
        sort_col = sort_col.desc() if order.lower() == "desc" else sort_col.asc()
        stmt = stmt.order_by(sort_col).limit(limit).offset(offset)
        items = self.db.execute(stmt).scalars().all()
        return items, total

    def create(self, *, organization_id: UUID, name: str, description: str | None) -> Project:
        project = Project(organization_id=organization_id, name=name, description=description)
        self.db.add(project)
        self.db.flush()
        return project

    def update(self, project: Project, *, name: str | None, description: str | None) -> Project:
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        self.db.flush()
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.flush()


