from database.operations.interface import Interface
from database.models.metric.table import TableMetric


class TableMetricRepository(Interface[TableMetric]):
    def __init__(self, db):
        super().__init__(TableMetric, db)
