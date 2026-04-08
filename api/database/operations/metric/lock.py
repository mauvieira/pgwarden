from database.operations.interface import Interface
from database.models.metric.lock import LockMetric


class LockMetricRepository(Interface[LockMetric]):
    def __init__(self, db):
        super().__init__(LockMetric, db)
