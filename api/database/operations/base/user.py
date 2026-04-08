from typing import Optional

from database.models.base import User
from database.operations import Interface


class UserRepository(Interface[User]):
    def __init__(self, db):
        super().__init__(User, db)

    async def find_by_email(self, email: str) -> Optional[User]:
        return await self.find_one_by(email=email)

    async def find_by_id(self, id: int) -> Optional[User]:
        return await self.find_one_by(id=id)

    async def find_by_name(self, name: str) -> Optional[User]:
        return await self.find_one_by(name=name)