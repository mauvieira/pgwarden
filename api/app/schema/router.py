from uuid import UUID
from fastapi import APIRouter

from app.schema.models import SchemaResponse
from app.schema.services import get_database_schema
from database.connection import DatabaseConnection

router = APIRouter(
    prefix="/schema",
    tags=["schema"]
)

@router.get("/{database_public_id}", response_model=SchemaResponse)
async def get_schema(database_public_id: UUID):
    async with DatabaseConnection() as conn:
        return await get_database_schema(conn, database_public_id)
