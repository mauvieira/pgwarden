from database.operations.interface import Interface
from database.models.collector.server import Server


class ServerRepository(Interface[Server]):
    def __init__(self, db):
        super().__init__(Server, db)
