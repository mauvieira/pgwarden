from datetime import datetime, timezone

import psutil

from database import DatabaseConnection, load_storage_query
from collector.collectors.server.base import BaseServerCollector
from log import logger


_INSERT_RAM = load_storage_query(schema="metric", table="ram", query_type="INSERT", query_name="default")


class RamCollector(BaseServerCollector):

    def __init__(self, metrics_db: DatabaseConnection, server_id: int) -> None:
        super().__init__(metrics_db=metrics_db, server_id=server_id)

    async def _collect(self) -> None:
        collected_at = datetime.now(timezone.utc)

        mem = psutil.virtual_memory()

        async with self.metrics_db as conn:
            async with conn.cursor() as cur:
                await cur.execute(_INSERT_RAM, {
                    "collected_at": collected_at,
                    "server_id": self.server_id,
                    "total_bytes": mem.total,
                    "used_bytes": mem.used,
                    "available_bytes": mem.available,
                    "percent": mem.percent,
                })
            await conn.commit()

        await logger.info("RamCollector", "collect", f"server_id={self.server_id} ram={mem.percent}%")
