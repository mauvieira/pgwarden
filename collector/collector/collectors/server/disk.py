from datetime import datetime, timezone

import psutil

from database import DatabaseConnection, load_storage_query
from collector.collectors.server.base import BaseServerCollector
from log import logger


_INSERT_DISK = load_storage_query(schema="metric", table="disk", query_type="INSERT", query_name="default")


class DiskCollector(BaseServerCollector):

    def __init__(self, metrics_db: DatabaseConnection, server_id: int) -> None:
        super().__init__(metrics_db=metrics_db, server_id=server_id)

    async def _collect(self) -> None:
        collected_at = datetime.now(timezone.utc)

        partitions = psutil.disk_partitions(all=False)
        to_insert = []

        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except PermissionError:
                continue

            to_insert.append({
                "collected_at": collected_at,
                "server_id": self.server_id,
                "mount_point": part.mountpoint,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent": usage.percent,
            })

        if to_insert:
            async with self.metrics_db as conn:
                async with conn.cursor() as cur:
                    await cur.executemany(_INSERT_DISK, to_insert)
                await conn.commit()

        await logger.info(
            "DiskCollector", "collect",
            f"server_id={self.server_id} partitions={len(to_insert)}"
        )
