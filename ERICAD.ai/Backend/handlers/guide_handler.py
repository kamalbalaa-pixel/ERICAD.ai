"""
Guide Handler
Handles requests to generate step-by-step guides.
"""

import json
from fastapi import WebSocket

from ai_service import generate_guide_steps
from utils import get_string_field, send_error, send_thinking


async def handle_guide_request(
    websocket: WebSocket,
    data: dict
) -> bool:
    """
    Handle a request to generate a step-by-step guide.
    
    Args:
        websocket: The WebSocket connection.
        data: The parsed JSON message data.
        
    Returns:
        True if message was handled, False if should continue to next iteration.
    """
    # Handle case-insensitive fields (C# serialization may vary)
    context = get_string_field(data, "context", "Context")
    
    if not context:
        await send_error(
            websocket,
            "No conversation to create guide from. Ask a question first."
        )
        return False
    
    await send_thinking(websocket, "📋 Creating step-by-step guide...")
    
    try:
        step_data = await generate_guide_steps(context)
        steps = step_data.get("steps", [])
        
        if not steps:
            await send_error(
                websocket,
                "Could not extract steps. Try asking a more specific question."
            )
            return False
        
        await websocket.send_text(json.dumps({
            "type": "guide_steps",
            "steps": steps,
            "message": f"📋 Guide ready with {len(steps)} steps"
        }))
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        await send_error(
            websocket,
            "Could not create guide. Try rephrasing your question."
        )
    except Exception as e:
        print(f"Guide error: {e}")
        await send_error(websocket, f"Guide error: {str(e)}")
    
    return True

