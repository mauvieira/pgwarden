import os
from contextlib import asynccontextmanager
from urllib.parse import quote_plus
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from passlib.context import CryptContext

from app.auth.router import router as auth_router
from app.schema.router import router as schema_router
from app.schema.exceptions import BaseAppException
from database.connection import DatabaseConnection
from database.models.base import User
from database.operations.base.user import UserRepository
from utils import get_env_var
from yoyo import read_migrations, get_backend


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def run_migrations() -> None:
    print("Starting database migrations (api)")
    host = get_env_var("DB_HOST")
    port = get_env_var("DB_PORT")
    user = get_env_var("DB_USER")
    password = quote_plus(get_env_var("DB_PASSWORD"))
    dbname = get_env_var("DB_NAME")

    db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
    migrations_dir = os.path.join(os.path.dirname(__file__), "database", "migrations")

    backend = get_backend(db_url, migration_table='_yoyo_migration_api')
    migrations = read_migrations(migrations_dir)

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
    print("Migrations completed successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()

    email = os.getenv("PGWARDEN_EMAIL", "admin@pgwarden.com")
    password = os.getenv("PGWARDEN_PASSWORD", "admin")
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

app = FastAPI(lifespan=lifespan)

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

app.include_router(auth_router)
app.include_router(schema_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, log_level="info", reload=True)
