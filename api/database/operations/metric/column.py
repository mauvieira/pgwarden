from database.operations.interface import Interface
from database.models.metric.column import ColumnMetric


class ColumnMetricRepository(Interface[ColumnMetric]):
    def __init__(self, db):
        super().__init__(ColumnMetric, db)
