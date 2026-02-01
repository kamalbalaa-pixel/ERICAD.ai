"""
Frames Handler
Handles video frame upload and encoding messages.
"""

import base64
from fastapi import WebSocket

from models import SessionData
from video_utils import get_fps_for_duration, encode_frames_to_mp4, format_duration
from utils import (
    get_list_field,
    get_int_field,
    get_bool_field,
    get_string_field,
    send_response,
    send_error,
)


async def handle_frames(
    websocket: WebSocket,
    data: dict,
    session: SessionData
) -> None:
    """
    Handle a frames upload message. Encodes frames to MP4 video.
    
    Args:
        websocket: The WebSocket connection.
        data: The parsed JSON message data.
        session: The current session data.
    """
    # Handle case-insensitive fields (C# serialization may vary)
    frames_data = get_list_field(data, "frames", "Frames")
    duration = get_int_field(data, "duration", "Duration")
    frame_count = get_int_field(data, "frameCount", "FrameCount")
    has_annotations = get_bool_field(data, "hasAnnotations", "HasAnnotations")
    
    if frames_data:
        # Decode frames
        frames = []
        total_size = 0
        
        for frame in frames_data:
            # Handle case-insensitive fields (C# serialization may vary)
            frame_data_str = get_string_field(frame, "data", "Data")
            frame_bytes = base64.b64decode(frame_data_str)
            total_size += len(frame_bytes)
            
            frames.append({
                "data": frame_bytes,
                "timestamp": get_string_field(frame, "timestamp", "Timestamp"),
                "hasAnnotations": get_bool_field(frame, "hasAnnotations", "HasAnnotations"),
            })
        
        # Encode frames to MP4
        fps = get_fps_for_duration(duration)
        print(f"Encoding {len(frames)} frames to MP4 at {fps} FPS...")
        
        video_bytes = encode_frames_to_mp4(frames, duration)
        
        if video_bytes:
            session.video_bytes = video_bytes
            session.is_video_mode = True
            session.video_duration = duration
            session.video_fps = fps
            session.has_annotations = has_annotations
            session.image_bytes = frames[-1]["data"] if frames else None  # Keep last frame as fallback
            session.media_analyzed = False  # Reset for new media
            
            # Save video for debugging
            with open("captured_video.mp4", "wb") as f:
                f.write(video_bytes)
            
            # Save last frame for debugging
            if frames:
                with open("captured_image.png", "wb") as f:
                    f.write(frames[-1]["data"])
            
            annotation_status = " (with annotations)" if has_annotations else ""
            video_size_mb = len(video_bytes) / (1024 * 1024)
            duration_str = format_duration(duration)
            print(f"Video encoded: {duration_str} at {fps} FPS, {video_size_mb:.1f} MB{annotation_status}")
            
            await send_response(
                websocket,
                "video_received",
                f"🎬 Video encoded: {duration_str} at {fps} FPS ({video_size_mb:.1f} MB){annotation_status}. Send a message to ask about it!"
            )
        else:
            await send_error(websocket, "Error: Failed to encode video")
    else:
        await send_error(websocket, "Error: No frame data received")

