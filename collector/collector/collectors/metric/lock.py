from datetime import datetime, timezone

from psycopg.rows import dict_row

from database import (
    DatabaseConnection, load_monitored_query,
    load_storage_query
)
from collector.collectors.base import BaseCollector
from collector.collectors.result import SyncResult
from log import logger


_COLLECT_LOCKS = load_monitored_query("locks_detail")
_INSERT_LOCK = load_storage_query(schema="metric", table="lock", query_type="INSERT", query_name="default")
_SELECT_TRACKED_TB = load_storage_query(schema="metadata", table="table", query_type="SELECT", query_name="by_database_id_and_active")
_SELECT_TRACKED_DB = load_storage_query(schema="metadata", table="database", query_type="SELECT", query_name="by_id")

class LockMetricCollector(BaseCollector):
    def __init__(self, monitored_db: DatabaseConnection, metrics_db: DatabaseConnection, db_id: int) -> None:
        super().__init__(monitored_db=monitored_db, metrics_db=metrics_db)
        self._db_id = db_id

    async def _collect(self) -> SyncResult:
        result = SyncResult()
        try:
            oid_to_id_map = await self._fetch_table_mapping()
            db_info = await self._fetch_db_info()
            if not db_info: return result

            collected_at = datetime.now(timezone.utc)
            to_insert = []

            async with self.monitored_db as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(_COLLECT_LOCKS, {"database_oid": db_info["oid"]})
                    locks = await cur.fetchall()

            for l in locks:
                internal_table_id = oid_to_id_map.get(l["table_oid"])

                if not internal_table_id:
                    continue

                to_insert.append({
                    "collected_at": collected_at,
                    "database_id": self._db_id,
                    "holder_pid": l["holder_pid"],
                    "type": l["type"],
                    "mode": l["mode"],
                    "is_granted": l["is_granted"],
                    "table_id": internal_table_id,
                    "query_preview": l["query_preview"]
                })

            if to_insert:
                async with self.metrics_db as conn:
                    async with conn.cursor() as cur:
                        await cur.executemany(_INSERT_LOCK, to_insert)
                    await conn.commit()

            result.inserted = len(to_insert)
            await logger.info("LockMetricCollector", "locks", f"Collected {result.inserted} lock metrics (db_id={self._db_id})")
        except Exception as error:
            await logger.error("LockCollector", "locks", f"Failed: {error}")
            raise

        return result

    async def _fetch_table_mapping(self) -> dict[int, int]:
        async with self.metrics_db as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(_SELECT_TRACKED_TB, {"database_id": self._db_id})
                rows = await cur.fetchall()
                return {r["oid"]: r["id"] for r in rows}


    async def _fetch_db_info(self) -> dict | None:
        async with self.metrics_db as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(_SELECT_TRACKED_DB, {"database_id": self._db_id})
                return await cur.fetchone()