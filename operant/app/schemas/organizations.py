from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str
    created_at: datetime


class AddMemberRequest(BaseModel):
    email: str
    role: str = Field(default="MEMBER")


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_id: UUID
    plan: str


class ChangePlanRequest(BaseModel):
    plan: str = Field(pattern=r"^(FREE|PRO)$")


