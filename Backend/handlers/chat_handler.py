"""
Chat Handler
Handles chat messages and AI responses.
"""

from fastapi import WebSocket

from models import SessionData
from ai_service import generate_response, get_model_display_name
from utils import get_string_field, send_response, send_error, send_thinking


async def handle_chat(
    websocket: WebSocket,
    data: dict,
    session: SessionData
) -> bool:
    """
    Handle a chat message. Generates AI response.
    
    Args:
        websocket: The WebSocket connection.
        data: The parsed JSON message data.
        session: The current session data.
        
    Returns:
        True if message was handled, False if should continue to next iteration.
    """
    # Handle case-insensitive fields (C# serialization may vary)
    user_prompt = get_string_field(data, "message", "Message").strip()
    selected_model = get_string_field(data, "model", "Model") or "gemini-2.5-flash"
    
    if not user_prompt:
        await send_error(websocket, "Please enter a message")
        return False
    
    # Check if we have an image or video in the session
    if not session.has_media():
        await send_error(
            websocket,
            "⚠️ No image or video uploaded yet. Please capture something first."
        )
        return False
    
    # Add user message to chat history
    session.chat_history.append({"role": "user", "content": user_prompt})
    
    # Determine if this is first analysis or follow-up
    is_first_analysis = not session.media_analyzed
    model_display = get_model_display_name(selected_model)
    content_type = "video" if session.is_video_mode else "image"
    
    # Send appropriate thinking indicator
    if is_first_analysis:
        thinking_msg = f"🔍 Analyzing {content_type} with {model_display}..."
    else:
        thinking_msg = "💭 Thinking..."
    await send_thinking(websocket, thinking_msg)
    
    try:
        # Generate AI response
        gemini_response = await generate_response(session, user_prompt, selected_model)
        print(f"Gemini response: {gemini_response[:200]}...")
        
        # Mark media as analyzed after first successful response
        if is_first_analysis:
            session.media_analyzed = True
        
        # Add assistant response to chat history
        session.chat_history.append({"role": "assistant", "content": gemini_response})
        
        # Send response back to frontend
        await send_response(websocket, "response", gemini_response)
        
    except Exception as e:
        error_msg = f"AI error: {str(e)}"
        print(error_msg)
        await send_error(websocket, error_msg)
    
    return True

