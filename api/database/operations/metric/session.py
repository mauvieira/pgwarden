from database.operations.interface import Interface
from database.models.metric.session import SessionMetric


class SessionMetricRepository(Interface[SessionMetric]):
    def __init__(self, db):
        super().__init__(SessionMetric, db)
