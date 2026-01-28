from __future__ import annotations

from sqlalchemy.orm import Session

from operant.app.core.errors import ForbiddenError, NotFoundError
from operant.app.models.subscription import PLAN_LIMITS, Plan
from operant.app.repositories.project_repository import ProjectRepository
from operant.app.repositories.subscription_repository import SubscriptionRepository


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.projects = ProjectRepository(db)
        self.subscriptions = SubscriptionRepository(db)

    def list_projects(
        self,
        *,
        organization_id,
        q: str | None,
        sort: str,
        order: str,
        limit: int,
        offset: int,
    ):
        return self.projects.list_for_org(
            organization_id, q=q, sort=sort, order=order, limit=limit, offset=offset
        )

    def create_project(self, *, organization_id, name: str, description: str | None):
        sub = self.subscriptions.get_by_org(organization_id)
        plan = Plan(sub.plan) if sub else Plan.FREE
        limits = PLAN_LIMITS[plan]
        count = self.projects.count_for_org(organization_id)
        if count >= limits["max_projects"]:
            raise ForbiddenError("Limite de projetos do plano atingido")

        project = self.projects.create(organization_id=organization_id, name=name, description=description)
        self.db.commit()
        return project

    def get_project(self, *, project_id):
        project = self.projects.get(project_id)
        if project is None:
            raise NotFoundError("Projeto não encontrado")
        return project

    def get_project_for_org(self, *, project_id, organization_id):
        project = self.get_project(project_id=project_id)
        if project.organization_id != organization_id:
            raise ForbiddenError("Projeto não pertence à organização atual")
        return project

    def update_project(self, *, project_id, name: str | None, description: str | None):
        project = self.get_project(project_id=project_id)
        project = self.projects.update(project, name=name, description=description)
        self.db.commit()
        return project

    def delete_project(self, *, project_id):
        project = self.get_project(project_id=project_id)
        self.projects.delete(project)
        self.db.commit()


