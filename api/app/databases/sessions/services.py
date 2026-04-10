import asyncio
import json
from datetime import datetime

from sqlalchemy import select, desc

from database.connection import DatabaseConnection
from database.models.metric.session import SessionMetric


def serialize_row(row) -> dict:
    data = {}
    for key, value in row.__dict__.items():
        if key.startswith("_"):
            continue
        if isinstance(value, datetime):
            data[key] = value.isoformat()
        else:
            data[key] = value
    return data


async def session_stream(database_id: int):
    last_ts = None

    while True:
        try:
            async with DatabaseConnection() as conn:
                result = await conn.execute(
                    select(SessionMetric)
                    .where(SessionMetric.database_id == database_id)
                    .order_by(desc(SessionMetric.collected_at))
                    .limit(1)
                )
                latest = result.scalar_one_or_none()

                if latest and (last_ts is None or latest.collected_at > last_ts):
                    last_ts = latest.collected_at
                    rows_result = await conn.execute(
                        select(SessionMetric)
                        .where(
                            SessionMetric.database_id == database_id,
                            SessionMetric.collected_at == last_ts,
                        )
                    )
                    rows = rows_result.scalars().all()
                    payload = [serialize_row(r) for r in rows]
                    yield {"event": "sessions", "data": json.dumps(payload)}

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

        await asyncio.sleep(2)
