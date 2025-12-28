"""
ERICAD AI Service
Handles all interactions with the Gemini AI API.
"""

from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    SYSTEM_PROMPT_BASE,
    SYSTEM_PROMPT_WITH_ANNOTATIONS,
    SYSTEM_PROMPT_VIDEO,
    SYSTEM_PROMPT_VIDEO_WITH_ANNOTATIONS,
)
from models import SessionData


# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


def get_model_display_name(model: str) -> str:
    """Get a human-readable name for the model."""
    if "3" in model:
        return "Gemini 3 Pro"
    return "Gemini 2.5 Flash"


def build_first_analysis_contents(
    session: SessionData,
    user_prompt: str
) -> list:
    """
    Build the content list for the first analysis of media.
    
    Args:
        session: The current session data.
        user_prompt: The user's question.
        
    Returns:
        List of content parts for the Gemini API.
    """
    contents = []
    
    if session.is_video_mode and session.video_bytes:
        # Video mode: send MP4 video
        system_prompt = (
            SYSTEM_PROMPT_VIDEO_WITH_ANNOTATIONS 
            if session.has_annotations 
            else SYSTEM_PROMPT_VIDEO
        )
        
        duration_str = (
            f"{session.video_duration // 60}:{session.video_duration % 60:02d}" 
            if session.video_duration >= 60 
            else f"{session.video_duration}s"
        )
        
        full_prompt = f"""{system_prompt}

This is a {duration_str} video recording at {session.video_fps} FPS.

User's question: {user_prompt}

Watch the video and respond to the user's question."""
        
        contents.append(full_prompt)
        
        # Add video
        video_part = types.Part.from_bytes(
            data=session.video_bytes,
            mime_type="video/mp4"
        )
        contents.append(video_part)
    else:
        # Single image mode
        system_prompt = (
            SYSTEM_PROMPT_WITH_ANNOTATIONS 
            if session.has_annotations 
            else SYSTEM_PROMPT_BASE
        )
        
        full_prompt = f"""{system_prompt}

User's question: {user_prompt}

Analyze the screenshot and respond to the user's question."""
        
        image_part = types.Part.from_bytes(
            data=session.image_bytes,
            mime_type="image/jpeg"
        )
        contents = [full_prompt, image_part]
    
    return contents


def build_followup_contents(session: SessionData, user_prompt: str) -> list:
    """
    Build the content list for a follow-up question (no media re-upload).
    
    Args:
        session: The current session data.
        user_prompt: The user's question.
        
    Returns:
        List of content parts for the Gemini API.
    """
    history_text = (
        "You are ERICAD, an expert assistant. "
        "Continue the conversation based on your previous analysis.\n\n"
    )
    history_text += "Previous conversation:\n"
    
    for msg in session.chat_history[:-1]:  # Exclude current message
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n\n"
    
    history_text += f"User's new question: {user_prompt}\n\n"
    history_text += "Respond based on your previous analysis of the content."
    
    return [history_text]


async def generate_response(
    session: SessionData,
    user_prompt: str,
    model: str
) -> str:
    """
    Generate an AI response for the user's prompt.
    
    Args:
        session: The current session data.
        user_prompt: The user's question.
        model: The Gemini model to use.
        
    Returns:
        The AI's response text.
    """
    is_first_analysis = not session.media_analyzed
    
    if is_first_analysis:
        contents = build_first_analysis_contents(session, user_prompt)
    else:
        contents = build_followup_contents(session, user_prompt)
    
    # Call Gemini API
    response = client.models.generate_content(
        model=model,
        contents=contents
    )
    
    return response.text


async def generate_guide_steps(context: str) -> dict:
    """
    Generate structured step-by-step guide from AI response.
    
    Args:
        context: The previous AI response to extract steps from.
        
    Returns:
        Dictionary with 'steps' list or raises exception.
    """
    from config import SYSTEM_PROMPT_GUIDE_STEPS
    import json
    
    guide_prompt = f"""{SYSTEM_PROMPT_GUIDE_STEPS}

Previous AI response to extract steps from:
{context}

Extract the actionable steps from this response. Return ONLY valid JSON."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[guide_prompt]
    )
    
    response_text = response.text.strip()
    
    # Clean up JSON if wrapped in markdown
    if "```" in response_text:
        parts = response_text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                response_text = part
                break
    
    return json.loads(response_text)

