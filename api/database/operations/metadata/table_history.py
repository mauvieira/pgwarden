from database.operations.interface import Interface
from database.models.metadata.table_history import TableHistory


class TableHistoryRepository(Interface[TableHistory]):
    def __init__(self, db):
        super().__init__(TableHistory, db)
