from database.operations.interface import Interface
from database.models.metadata.database import Database


class DatabaseRepository(Interface[Database]):
    def __init__(self, db):
        super().__init__(Database, db)
