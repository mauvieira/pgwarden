from typing import List
from fastapi import APIRouter, HTTPException

from app.database.models import DatabaseListItem, DatabaseCreate
from database.connection import DatabaseConnection
from database.operations.metadata.database import DatabaseRepository
from database.operations.collector.server import ServerRepository
from database.models.metadata.database import Database
from utils import encrypt, decrypt


router = APIRouter(
    prefix="/database",
    tags=["database"]
)

@router.post(
    "/",
    summary="Register a new managed database",
    description="Registers a new monitored database and links it to an existing PostgreSQL server. The database name is securely encrypted.",
)
async def create_database(db_in: DatabaseCreate):
    async with DatabaseConnection() as conn:
        server_repo = ServerRepository(conn)
        db_repo = DatabaseRepository(conn)
        
        server = await server_repo.find_one_by(public_id=db_in.server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
            
        new_db = Database(
            server_id=server.id,
            db_name=encrypt(db_in.db_name)
        )
        
        saved_db = await db_repo.insert(new_db)
        return {"message": "Database created successfully", "id": saved_db.public_id}

@router.get(
    "/",
    response_model=List[DatabaseListItem],
    summary="List all managed databases",
    description="Returns a list of all managed databases and their connection status. Includes both active and soft-deleted databases.",
)
async def list_databases():
    async with DatabaseConnection() as conn:
        repo = DatabaseRepository(conn)
        databases = await repo.find_all()
        
        return [
            DatabaseListItem(
                id=db.public_id,
                name=decrypt(db.db_name),
                status=db.deleted_at is None
            )
            for db in databases
        ]
