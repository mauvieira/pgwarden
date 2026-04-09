from uuid import UUID

from pydantic import BaseModel


class DatabaseCreate(BaseModel):
    server_id: UUID
    db_name: str

class DatabaseListItem(BaseModel):
    id: UUID
    name: str
    status: bool

    class Config:
        from_attributes = True
