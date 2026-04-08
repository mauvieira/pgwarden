from database.operations.interface import Interface
from database.models.metadata.table import Table


class TableRepository(Interface[Table]):
    def __init__(self, db):
        super().__init__(Table, db)
