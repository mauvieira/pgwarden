from database.operations.interface import Interface
from database.models.metadata.index import Index


class IndexRepository(Interface[Index]):
    def __init__(self, db):
        super().__init__(Index, db)
