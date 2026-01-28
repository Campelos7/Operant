from __future__ import annotations

from sqlalchemy.orm import Session

from operant.app.core.errors import NotFoundError
from operant.app.repositories.task_repository import TaskRepository


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.tasks = TaskRepository(db)

    def list_tasks(
        self,
        *,
        project_id,
        status: str | None,
        sort: str,
        order: str,
        limit: int,
        offset: int,
    ):
        return self.tasks.list_for_project(
            project_id, status=status, sort=sort, order=order, limit=limit, offset=offset
        )

    def create_task(self, *, project_id, title: str, description: str | None, status: str):
        task = self.tasks.create(project_id=project_id, title=title, description=description, status=status)
        self.db.commit()
        return task

    def get_task(self, *, task_id):
        task = self.tasks.get(task_id)
        if task is None:
            raise NotFoundError("Tarefa não encontrada")
        return task

    def update_task(self, *, task_id, title: str | None, description: str | None, status: str | None):
        task = self.get_task(task_id=task_id)
        task = self.tasks.update(task, title=title, description=description, status=status)
        self.db.commit()
        return task

    def delete_task(self, *, task_id):
        task = self.get_task(task_id=task_id)
        self.tasks.delete(task)
        self.db.commit()


