from database.operations.interface import Interface
from database.models.metadata.column import ColumnModel


class ColumnRepository(Interface[ColumnModel]):
    def __init__(self, db):
        super().__init__(ColumnModel, db)
