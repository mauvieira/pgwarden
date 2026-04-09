from abc import ABC, abstractmethod

from database import DatabaseConnection
from log import logger


class BaseServerCollector(ABC):

    def __init__(
        self,
        metrics_db: DatabaseConnection,
        server_id:  int,
    ) -> None:
        self.metrics_db = metrics_db
        self.server_id  = server_id

    async def collect(self) -> None:
        try:
            await self._collect()
        except Exception as error:
            await logger.error(
                self.__class__.__name__,
                "collect",
                f"Unhandled error (server_id={self.server_id}): {error}",
            )
            raise

    @abstractmethod
    async def _collect(self) -> None: ...
