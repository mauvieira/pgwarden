from datetime import datetime, timezone

import psutil

from database import DatabaseConnection, load_storage_query
from collector.collectors.server.base import BaseServerCollector
from log import logger


_INSERT_CPU = load_storage_query(schema="metric", table="cpu", query_type="INSERT", query_name="default")


class CpuCollector(BaseServerCollector):

    def __init__(self, metrics_db: DatabaseConnection, server_id: int) -> None:
        super().__init__(metrics_db=metrics_db, server_id=server_id)

    async def _collect(self) -> None:
        collected_at = datetime.now(timezone.utc)

        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=True)

        async with self.metrics_db as conn:
            async with conn.cursor() as cur:
                await cur.execute(_INSERT_CPU, {
                    "collected_at": collected_at,
                    "server_id": self.server_id,
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                })
            await conn.commit()

        await logger.info("CpuCollector", "collect", f"server_id={self.server_id} cpu={cpu_percent}%")
