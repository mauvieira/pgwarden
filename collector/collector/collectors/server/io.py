from datetime import datetime, timezone

import psutil

from database import DatabaseConnection, load_storage_query
from collector.collectors.server.base import BaseServerCollector
from log import logger


_INSERT_IO = load_storage_query(schema="metric", table="io", query_type="INSERT", query_name="default")


class IoCollector(BaseServerCollector):

    def __init__(self, metrics_db: DatabaseConnection, server_id: int) -> None:
        super().__init__(metrics_db=metrics_db, server_id=server_id)

    async def _collect(self) -> None:
        collected_at = datetime.now(timezone.utc)

        counters = psutil.disk_io_counters()

        if not counters:
            await logger.info("IoCollector", "collect", f"server_id={self.server_id} no I/O counters available")
            return

        async with self.metrics_db as conn:
            async with conn.cursor() as cur:
                await cur.execute(_INSERT_IO, {
                    "collected_at": collected_at,
                    "server_id": self.server_id,
                    "read_bytes": counters.read_bytes,
                    "write_bytes": counters.write_bytes,
                    "read_count": counters.read_count,
                    "write_count": counters.write_count,
                })
            await conn.commit()

        await logger.info(
            "IoCollector", "collect",
            f"server_id={self.server_id} read={counters.read_bytes}B write={counters.write_bytes}B"
        )
