from psycopg.rows import dict_row

from database import load_storage_query
from log import logger
from utils import encrypt, decrypt


async def _upsert_server(conn, entry: dict) -> int:
    name = entry["name"]

    async with conn.cursor() as cur:
        await cur.execute(load_storage_query(schema="collector", table="server", query_type="INSERT", query_name="default"), {
            "name":     name,
            "host":     encrypt(entry["host"]),
            "port":     encrypt(str(entry.get("port", 5432))),
            "username": encrypt(entry["username"]),
            "password": encrypt(entry["password"]),
            "ssl_mode": entry.get("ssl_mode", "prefer"),
        })

    async with conn.cursor() as cur:
        await cur.execute(load_storage_query(schema="collector", table="server", query_type="SELECT", query_name="by_name"), {"name": name})
        existing = await cur.fetchone()

    await logger.info("Bootstrap", name, f"Server registered (id={existing})")
    return existing["id"]


async def _upsert_database(conn, server_id: int, db_name: str) -> None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(load_storage_query(schema="metadata", table="database", query_type="SELECT", query_name="by_server_id"), {"server_id": server_id})
        existing_dbs = await cur.fetchall()

    for row in existing_dbs:
        try:
            if decrypt(row["db_name"]) == db_name:
                await logger.info("Bootstrap", "Insert", f"server_id={server_id} '{db_name}' already registered — skipping")
                return
        except Exception as error:
            await logger.error("Bootstrap", "Insert", error)
            continue

    async with conn.cursor() as cur:
        await cur.execute(load_storage_query(schema="metadata", table="database", query_type="INSERT", query_name="default"), {
            "server_id": server_id,
            "db_name":   encrypt(db_name),
        })
        row = await cur.fetchone()

    await logger.info("Bootstrap", "Insert", f"server_id={server_id} '{db_name}' registered (id={row[0]})")