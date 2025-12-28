"""
Image Handler
Handles single image upload messages.
"""

import base64
from fastapi import WebSocket

from models import SessionData
from utils import get_string_field, get_bool_field, send_response, send_error


async def handle_image(
    websocket: WebSocket,
    data: dict,
    session: SessionData
) -> None:
    """
    Handle an image upload message.
    
    Args:
        websocket: The WebSocket connection.
        data: The parsed JSON message data.
        session: The current session data.
    """
    # Handle case-insensitive fields (C# serialization may vary)
    image_data = get_string_field(data, "data", "Data")
    has_annotations = get_bool_field(data, "hasAnnotations", "HasAnnotations")
    
    if image_data:
        session.image_bytes = base64.b64decode(image_data)
        session.has_annotations = has_annotations
        session.is_video_mode = False
        session.video_bytes = None
        session.media_analyzed = False  # Reset for new media
        
        # Save image to file for debugging
        with open("captured_image.png", "wb") as f:
            f.write(session.image_bytes)
        
        annotation_status = " (with annotations)" if has_annotations else ""
        print(f"Image stored in session{annotation_status}")
        
        # Confirm receipt - don't auto-analyze
        size_kb = len(session.image_bytes) // 1024
        await send_response(
            websocket,
            "image_received",
            f"📷 Image received ({size_kb} KB){annotation_status}. Send a message to ask about it!"
        )
    else:
        await send_error(websocket, "Error: No image data received")

