from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DatabaseCreate(BaseModel):
    server_id: UUID
    db_name: str


class DatabaseCreatedResponse(BaseModel):
    message: str
    id: UUID


class DatabaseListItem(BaseModel):
    id: UUID
    name: str
    status: bool

    model_config = ConfigDict(from_attributes=True)
