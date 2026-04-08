from database.operations.interface import Interface
from database.models.metadata.column_history import ColumnHistory


class ColumnHistoryRepository(Interface[ColumnHistory]):
    def __init__(self, db):
        super().__init__(ColumnHistory, db)
