from datetime import datetime, timezone

from psycopg.rows import dict_row

from database import DatabaseConnection, load_monitored_query, load_storage_query
from collector.collectors.base import BaseCollector
from collector.collectors.result import SyncResult
from log import logger


_COLLECT_IDX_METRICS = load_monitored_query("indexes_detail")
_INSERT_IDX_METRIC = load_storage_query(schema="metric", table="index", query_type="INSERT", query_name="default")
_SELECT_TRACKED_INDEX = load_storage_query(schema="metadata", table="index", query_type="SELECT", query_name="by_database_id_and_active")

class IndexMetricCollector(BaseCollector):

    def __init__(
        self,
        monitored_db: DatabaseConnection,
        metrics_db: DatabaseConnection,
        db_id: int,
    ) -> None:
        super().__init__(monitored_db=monitored_db, metrics_db=metrics_db)
        self._db_id = db_id

    async def _collect(self) -> SyncResult:
        await logger.info("IndexMetricCollector", "indexes", f"Starting (db_id={self._db_id})")
        result = SyncResult()

        try:
            idx_map, index_oids = await self._fetch_index_mapping()

            if not index_oids:
                await logger.info("IndexMetricCollector", "indexes", "No tracked indexes. Skipping.")
                return result

            collected_at = datetime.now(timezone.utc)

            async with self.monitored_db as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(_COLLECT_IDX_METRICS, {"index_oids": list(index_oids)})
                    idx_metrics = await cur.fetchall()

            to_insert = []
            for row in idx_metrics:
                idx_id = idx_map.get(row["index_oid"])
                if idx_id:
                    to_insert.append({
                        "collected_at": collected_at,
                        "index_id": idx_id,
                        "size": row["index_size"],
                        "scan_qt": row["idx_scan"],
                        "tup_read_qt": row["idx_tup_read"],
                        "tup_fetch_qt": row["idx_tup_fetch"],
                        "blks_read": row["blks_read"],
                        "blks_hit": row["blks_hit"]
                    })

            async with self.metrics_db as conn:
                async with conn.cursor() as cur:
                    if to_insert:
                        await cur.executemany(_INSERT_IDX_METRIC, to_insert)
                await conn.commit()

            result.inserted = len(to_insert)
            await logger.info("IndexMetricCollector", "indexes", str(result))

        except Exception as error:
            await logger.error("IndexMetricCollector", "indexes", f"Failed (db_id={self._db_id}): {error}")
            raise

        return result

    async def _fetch_index_mapping(self) -> tuple[dict[int, int], set[int]]:
        async with self.metrics_db as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(_SELECT_TRACKED_INDEX, {"database_id": self._db_id})
                rows = await cur.fetchall()
                mapping = {r["oid"]: r["id"] for r in rows}
                oids = {r["oid"] for r in rows}
                return mapping, oids