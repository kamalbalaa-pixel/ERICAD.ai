"""
ERICAD Backend Models
Data classes and session management.
"""

from typing import Optional


class SessionData:
    """
    Stores session data for each WebSocket connection.
    Maintains image/video data, chat history, and analysis state.
    """
    
    def __init__(self):
        # Media storage
        self.image_bytes: Optional[bytes] = None
        self.video_bytes: Optional[bytes] = None  # MP4 video data
        
        # Media metadata
        self.has_annotations: bool = False
        self.is_video_mode: bool = False  # True if we have video, False if single image
        self.video_duration: int = 0  # Duration in seconds
        self.video_fps: int = 0  # FPS of the encoded video
        
        # Chat state
        self.chat_history: list = []
        self.media_analyzed: bool = False  # True after first analysis of current media
    
    def clear(self):
        """Reset all session data for a fresh start."""
        self.image_bytes = None
        self.video_bytes = None
        self.is_video_mode = False
        self.video_duration = 0
        self.video_fps = 0
        self.has_annotations = False
        self.chat_history = []
        self.media_analyzed = False
    
    def has_media(self) -> bool:
        """Check if session has any uploaded media."""
        return self.image_bytes is not None or self.video_bytes is not None


# Global session storage for active WebSocket connections
active_sessions: dict[int, SessionData] = {}


def get_session(session_id: int) -> SessionData:
    """Get or create a session for the given ID."""
    if session_id not in active_sessions:
        active_sessions[session_id] = SessionData()
    return active_sessions[session_id]


def remove_session(session_id: int) -> None:
    """Remove a session when the connection closes."""
    if session_id in active_sessions:
        del active_sessions[session_id]

