from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from operant.app.core.errors import ForbiddenError, UnauthorizedError
from operant.app.core.permissions import OrgRole, has_min_role
from operant.app.core.security import InvalidTokenError, decode_access_token
from operant.app.db.session import get_db
from operant.app.repositories.membership_repository import MembershipRepository
from operant.app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user(
    db: Session = Depends(db_session),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if creds is None or not creds.credentials:
        raise UnauthorizedError("Não autenticado")
    try:
        user_id, _jti = decode_access_token(creds.credentials)
    except InvalidTokenError as e:
        raise UnauthorizedError(str(e)) from e

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Usuário inválido ou inativo")
    return user


def get_org_id(x_organization_id: str | None = Header(default=None, alias="X-Organization-Id")) -> UUID:
    if not x_organization_id:
        raise ForbiddenError("Cabeçalho X-Organization-Id é obrigatório para este endpoint")
    try:
        return UUID(x_organization_id)
    except ValueError as e:
        raise ForbiddenError("X-Organization-Id inválido") from e


def get_current_membership(
    org_id: UUID = Depends(get_org_id),
    db: Session = Depends(db_session),
    user=Depends(get_current_user),
):
    membership = MembershipRepository(db).get_by_user_org(user.id, org_id)
    if membership is None:
        raise ForbiddenError("Sem acesso à organização")
    return membership


def require_min_org_role(min_role: OrgRole):
    def _dep(membership=Depends(get_current_membership)):
        actual = OrgRole(membership.role)
        if not has_min_role(actual, min_role):
            raise ForbiddenError("Permissão insuficiente")
        return membership

    return _dep


