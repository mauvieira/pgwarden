from database.operations.interface import Interface
from database.models.metadata.index_column import IndexColumn


class IndexColumnRepository(Interface[IndexColumn]):
    def __init__(self, db):
        super().__init__(IndexColumn, db)
