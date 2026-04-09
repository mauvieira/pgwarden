from datetime import datetime, timezone

from psycopg.rows import dict_row

from database import (
    DatabaseConnection, load_monitored_query,
    load_storage_query
)
from collector.collectors.base import BaseCollector
from collector.collectors.result import SyncResult
from log import logger


_COLLECT_SESSIONS = load_monitored_query("sessions_detail")
_INSERT_SESSION = load_storage_query(schema="metric", table="session", query_type="INSERT", query_name="default")
_SELECT_TRACKED_DB = load_storage_query(schema="metadata", table="database", query_type="SELECT", query_name="by_id")

class SessionMetricCollector(BaseCollector):
    def __init__(self, monitored_db: DatabaseConnection, metrics_db: DatabaseConnection, db_id: int) -> None:
        super().__init__(monitored_db=monitored_db, metrics_db=metrics_db)
        self._db_id = db_id

    async def _collect(self) -> SyncResult:
        result = SyncResult()
        try:
            db_info = await self._fetch_db_info()
            if not db_info: return result

            collected_at = datetime.now(timezone.utc)
            to_insert = []

            async with self.monitored_db as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(_COLLECT_SESSIONS, {"database_oid": db_info["oid"]})
                    sessions = await cur.fetchall()

            for s in sessions:
                to_insert.append({
                    "collected_at": collected_at,
                    "database_id": self._db_id,
                    "pid": s["pid"],
                    "backend_start": s["backend_start"],
                    "user_name": s["user_name"],
                    "application_name": s["application_name"],
                    "client_addr": s["client_addr"],
                    "state": s["state"],
                    "wait_event_type": s["wait_event_type"],
                    "wait_event": s["wait_event"],
                    "query_start": s["query_start"],
                    "state_change": s["state_change"],
                    "query_preview": s["query_preview"]
                })

            if to_insert:
                async with self.metrics_db as conn:
                    async with conn.cursor() as cur:
                        await cur.executemany(_INSERT_SESSION, to_insert)
                    await conn.commit()

            result.inserted = len(to_insert)
            await logger.info("SessionMetricCollector", "sessions", f"Collected {result.inserted} session metrics (db_id={self._db_id})")
        except Exception as error:
            await logger.error("SessionCollector", "sessions", f"Failed: {error}")
            raise

        return result

    async def _fetch_db_info(self) -> dict | None:
        async with self.metrics_db as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(_SELECT_TRACKED_DB, {"database_id": self._db_id})
                return await cur.fetchone()