import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProjectMemberAdd(BaseModel):
    user_id: uuid.UUID


class ProjectMemberRead(BaseModel):
    user_id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    role: str
    joined_at: datetime
