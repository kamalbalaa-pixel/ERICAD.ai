"""
ERICAD Video Utilities
Functions for encoding frames to video.
"""

import os
import tempfile
import cv2
import numpy as np


def get_fps_for_duration(duration_seconds: int) -> int:
    """
    Get the appropriate FPS based on recording duration.
    
    Args:
        duration_seconds: The duration of the recording in seconds.
        
    Returns:
        The recommended FPS for encoding.
    """
    if duration_seconds <= 60:
        return 3  # 15s - 60s: 3 FPS
    elif duration_seconds <= 180:
        return 2  # 1:30 - 3:00: 2 FPS
    else:
        return 1  # 3:30 - 7:30: 1 FPS


def encode_frames_to_mp4(frames: list[dict], duration_seconds: int) -> bytes:
    """
    Encode a list of JPEG frames into an MP4 video.
    
    Args:
        frames: List of frame dictionaries with 'data' (bytes) key.
        duration_seconds: Target duration for FPS calculation.
        
    Returns:
        MP4 video as bytes, or empty bytes if encoding fails.
    """
    if not frames:
        return b""
    
    fps = get_fps_for_duration(duration_seconds)
    
    # Decode first frame to get dimensions
    first_frame = cv2.imdecode(
        np.frombuffer(frames[0]["data"], dtype=np.uint8),
        cv2.IMREAD_COLOR
    )
    height, width = first_frame.shape[:2]
    
    # Calculate how many frames we need for the target FPS and duration
    total_frames_needed = fps * duration_seconds
    
    # Sample frames evenly if we have more than needed
    if len(frames) > total_frames_needed:
        step = len(frames) / total_frames_needed
        sampled_indices = [int(i * step) for i in range(total_frames_needed)]
        sampled_frames = [frames[i] for i in sampled_indices if i < len(frames)]
    else:
        sampled_frames = frames
    
    # Create temporary file for video
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        # Initialize video writer with H.264 codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        
        for frame_data in sampled_frames:
            # Decode JPEG to numpy array
            img = cv2.imdecode(
                np.frombuffer(frame_data["data"], dtype=np.uint8),
                cv2.IMREAD_COLOR
            )
            if img is not None:
                # Ensure frame matches expected dimensions
                if img.shape[:2] != (height, width):
                    img = cv2.resize(img, (width, height))
                out.write(img)
        
        out.release()
        
        # Read the video file back as bytes
        with open(temp_path, 'rb') as f:
            video_bytes = f.read()
        
        return video_bytes
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


def format_duration(seconds: int) -> str:
    """
    Format seconds into a human-readable duration string.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted string like "1:30" or "45s".
    """
    if seconds >= 60:
        return f"{seconds // 60}:{seconds % 60:02d}"
    return f"{seconds}s"

