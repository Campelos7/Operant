from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from operant.app.models.task import Task


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, task_id: UUID) -> Task | None:
        return self.db.get(Task, task_id)

    def list_for_project(
        self,
        project_id: UUID,
        *,
        status: str | None,
        sort: str,
        order: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        stmt = select(Task).where(Task.project_id == project_id)
        if status:
            stmt = stmt.where(Task.status == status)

        total = int(self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one())

        sort_col = Task.created_at if sort == "created_at" else Task.title
        sort_col = sort_col.desc() if order.lower() == "desc" else sort_col.asc()
        stmt = stmt.order_by(sort_col).limit(limit).offset(offset)
        items = self.db.execute(stmt).scalars().all()
        return items, total

    def create(self, *, project_id: UUID, title: str, description: str | None, status: str) -> Task:
        task = Task(project_id=project_id, title=title, description=description, status=status)
        self.db.add(task)
        self.db.flush()
        return task

    def update(self, task: Task, *, title: str | None, description: str | None, status: str | None) -> Task:
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status
        self.db.flush()
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.flush()


