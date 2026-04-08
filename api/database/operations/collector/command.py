from database.operations.interface import Interface
from database.models.collector.command import Command


class CommandRepository(Interface[Command]):
    def __init__(self, db):
        super().__init__(Command, db)
