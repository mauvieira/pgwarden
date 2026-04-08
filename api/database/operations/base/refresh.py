from typing import Optional

from sqlalchemy import select

from database.models.base import Refresh
from database.operations import Interface


class RefreshRepository(Interface[Refresh]):
    def __init__(self, db):
        super().__init__(Refresh, db)

    async def find_by_token(self, token: str) -> Optional[Refresh]:
        result = await self.db.execute(
            select(self.model).filter(self.model.token == token)
        )
        return result.scalar_one_or_none()