import os
import sys
from yoyo import read_migrations, get_backend

def run_migrations():
    print("Starting migrations...")
    
    # Environment variables
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_host = os.getenv("DB_HOST", "db")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "postgres")
    
    # Construct database URL
    # yoyo-migrations uses sqlalchemy-like URLs for backends
    # postgresql+psycopg is the driver name for psycopg 3
    db_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        backend = get_backend(db_url)
        # Read migrations from the current directory (where SQL files are located)
        migrations = read_migrations('.')
        
        if not migrations:
            print("No migrations found.")
            return

        with backend.lock():
            # Apply all pending migrations
            pending = backend.to_apply(migrations)
            if pending:
                print(f"Applying {len(pending)} pending migrations...")
                backend.apply_migrations(pending)
                print("Migrations applied successfully.")
            else:
                print("No pending migrations to apply.")
                
    except Exception as e:
        print(f"Error applying migrations: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
