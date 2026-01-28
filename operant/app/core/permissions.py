from __future__ import annotations

from enum import StrEnum


class OrgRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


ROLE_RANK: dict[OrgRole, int] = {
    OrgRole.OWNER: 3,
    OrgRole.ADMIN: 2,
    OrgRole.MEMBER: 1,
}


def has_min_role(actual: OrgRole, minimum: OrgRole) -> bool:
    return ROLE_RANK[actual] >= ROLE_RANK[minimum]


