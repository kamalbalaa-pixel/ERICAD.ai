"""
Session Handler
Handles session management messages.
"""

from fastapi import WebSocket

from models import SessionData
from utils import send_response


async def handle_new_session(
    websocket: WebSocket,
    session: SessionData,
    session_id: int
) -> None:
    """
    Handle a request to clear the session and start fresh.
    
    Args:
        websocket: The WebSocket connection.
        session: The current session data.
        session_id: The session identifier.
    """
    session.clear()
    print(f"Session {session_id} cleared")
    
    await send_response(
        websocket,
        "session_cleared",
        "🔄 Session cleared. Capture a new screenshot to begin."
    )

