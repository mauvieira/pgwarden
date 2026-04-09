import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from passlib.context import CryptContext

from app.auth.router import router as auth_router
from app.schema.router import router as schema_router
from app.database.router import router as database_router
from app.server.router import router as server_router
from app.schema.exceptions import BaseAppException
from database.connection import DatabaseConnection
from database.models.base import User
from database.operations.base.user import UserRepository


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@asynccontextmanager
async def lifespan(app: FastAPI):

    email = os.getenv("PGWARDEN_EMAIL")
    password = os.getenv("PGWARDEN_PASSWORD")
    hashed_password = pwd_context.hash(password)

    try:
        async with DatabaseConnection() as conn:
            user_repo = UserRepository(conn)
            existing_user = await user_repo.find_by_email(email)
            if not existing_user:
                admin_user = User(
                    email=email,
                    password=hashed_password,
                    name="Admin",
                    is_admin=True,
                )
                await user_repo.insert(admin_user)
                print(f"Admin user {email} created successfully.")
    except Exception as e:
        print(f"Failed to initialize admin user: {e}")
        
    yield

tags_metadata = [
    {
        "name": "auth",
        "description": "Authentication and authorization endpoints. Handles login and JWT token refresh.",
    },
    {
        "name": "servers",
        "description": "Manage registered PostgreSQL servers. Connection credentials are encrypted and stored securely.",
    },
    {
        "name": "databases",
        "description": "Manage monitored databases linked to the registered servers.",
    },
    {
        "name": "schemas",
        "description": "Expose the currently collected schema metadata (tables, columns, indexes).",
    },
]

app = FastAPI(
    title="PGWarden API",
    description="""
    PGWarden API provides endpoints for managing monitored PostgreSQL servers and databases. 
    """,
    version="0.1.0",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "defaultModelsExpandDepth": -1,
    },
    lifespan=lifespan
)

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "message": exc.message,
            "details": exc.details
        }
    )

app.include_router(auth_router, prefix="/v1")
app.include_router(schema_router, prefix="/v1")
app.include_router(database_router, prefix="/v1")
app.include_router(server_router, prefix="/v1")

