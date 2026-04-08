from datetime import datetime, timezone

from psycopg.rows import dict_row

from database import (
    DatabaseConnection, load_monitored_query,
    load_storage_query
)
from collector.collectors.base import BaseCollector
from collector.collectors.result import SyncResult
from log import logger


_COLLECT_COL_METRICS = load_monitored_query("columns_detail")
_INSERT_COL_METRIC = load_storage_query(schema="metric", table="column", query_type="INSERT", query_name="default")
_SELECT_TRACKED_COLUMN = load_storage_query(schema="metadata", table="column", query_type="SELECT", query_name="by_database_id_and_active")

class ColumnMetricCollector(BaseCollector):

    def __init__(
        self,
        monitored_db: DatabaseConnection,
        metrics_db: DatabaseConnection,
        db_id: int,
    ) -> None:
        super().__init__(monitored_db=monitored_db, metrics_db=metrics_db)
        self._db_id = db_id

    async def _collect(self) -> SyncResult:
        await logger.info("ColumnMetricCollector", "columns", f"Starting (db_id={self._db_id})")
        result = SyncResult()

        try:
            col_map, table_oids = await self._fetch_column_mapping()

            if not table_oids:
                await logger.info("ColumnMetricCollector", "columns", "No tracked tables. Skipping.")
                return result

            collected_at = datetime.now(timezone.utc)

            async with self.monitored_db as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(_COLLECT_COL_METRICS, {"table_oids": list(table_oids)})
                    col_metrics = await cur.fetchall()

            to_insert = []
            for row in col_metrics:
                col_id = col_map.get((row["table_oid"], row["column_attnum"]))
                if col_id:
                    to_insert.append({
                        "collected_at": collected_at,
                        "column_id": col_id,
                        "avg_width": row["avg_width"],
                        "null_fraction": row["null_fraction"],
                        "n_distinct": row["n_distinct"],
                        "estimated_size": row["estimated_size"]
                    })

            async with self.metrics_db as conn:
                async with conn.cursor() as cur:
                    if to_insert:
                        await cur.executemany(_INSERT_COL_METRIC, to_insert)
                await conn.commit()

            result.inserted = len(to_insert)
            await logger.info("ColumnMetricCollector", "columns", str(result))

        except Exception as error:
            await logger.error("ColumnMetricCollector", "columns", f"Failed (db_id={self._db_id}): {error}")
            raise

        return result

    async def _fetch_column_mapping(self) -> tuple[dict[tuple[int, int], int], set[int]]:
        async with self.metrics_db as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(_SELECT_TRACKED_COLUMN, {"database_id": self._db_id})
                rows = await cur.fetchall()
                mapping = {(r["table_oid"], r["attnum"]): r["id"] for r in rows}
                oids = {r["table_oid"] for r in rows}
                return mapping, oids