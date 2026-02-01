"""
ERICAD Message Handlers
Each handler manages a specific type of WebSocket message.
"""

from .image_handler import handle_image
from .frames_handler import handle_frames
from .chat_handler import handle_chat
from .guide_handler import handle_guide_request
from .session_handler import handle_new_session

__all__ = [
    "handle_image",
    "handle_frames",
    "handle_chat",
    "handle_guide_request",
    "handle_new_session",
]

