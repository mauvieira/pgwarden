from database.operations.interface import Interface
from database.models.collector.config import Config


class ConfigRepository(Interface[Config]):
    def __init__(self, db):
        super().__init__(Config, db)
