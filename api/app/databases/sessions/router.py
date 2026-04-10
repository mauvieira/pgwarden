from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.databases.sessions.services import session_stream
from app.auth.services import get_current_user


router = APIRouter(
    prefix="/databases/{database_id}/sessions",
    tags=["sessions"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/stream",
    summary="SSE stream of active sessions",
    description="Server-Sent Events endpoint that streams the latest collected sessions for a specific database. Updates every 3 seconds.",
)
async def stream_sessions(database_id: int):
    return EventSourceResponse(session_stream(database_id))
