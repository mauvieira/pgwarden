from database.operations.interface import Interface
from database.models.metric.index import IndexMetric


class IndexMetricRepository(Interface[IndexMetric]):
    def __init__(self, db):
        super().__init__(IndexMetric, db)
