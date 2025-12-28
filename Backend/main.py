"""
ERICAD Backend - Main Entry Point
FastAPI application with WebSocket support for the ERICAD overlay assistant.
"""

import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import SERVER_HOST, SERVER_PORT
from models import SessionData, get_session, remove_session
from utils import get_string_field, send_response, send_error
from handlers import (
    handle_image,
    handle_frames,
    handle_chat,
    handle_guide_request,
    handle_new_session,
)


# =============================================================================
# FastAPI Application Setup
# =============================================================================

app = FastAPI(
    title="ERICAD API",
    description="Backend API for ERICAD Project - AI-powered overlay assistant",
    version="1.0.0"
)

# Configure CORS for WPF client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HTTP Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint - API welcome message."""
    return {"message": "Welcome to ERICAD API"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time communication with the frontend.
    Handles all message types: image, frames, chat, guide requests, and session management.
    """
    await websocket.accept()
    session_id = id(websocket)
    session = get_session(session_id)
    print(f"WebSocket connection established (session: {session_id})")
    
    try:
        while True:
            message = await websocket.receive_text()
            
            # Try to parse as JSON
            try:
                data = json.loads(message)
                
                # Debug: print received keys to diagnose case sensitivity issues
                print(f"DEBUG: Received JSON keys: {list(data.keys())}")
                
                # Handle case-insensitive type field (C# might send "Type" instead of "type")
                msg_type = get_string_field(data, "type", "Type")
                
                # Route to appropriate handler
                if msg_type == "image":
                    await handle_image(websocket, data, session)
                
                elif msg_type == "frames":
                    await handle_frames(websocket, data, session)
                
                elif msg_type == "chat":
                    await handle_chat(websocket, data, session)
                
                elif msg_type == "request_guide":
                    await handle_guide_request(websocket, data)
                
                elif msg_type == "new_session":
                    await handle_new_session(websocket, session, session_id)
                
                else:
                    # Handle unknown message types
                    print(f"Received unknown message type: {msg_type}")
                    await send_response(
                        websocket,
                        "info",
                        f"Received {msg_type} message"
                    )
                    
            except json.JSONDecodeError:
                # Not JSON, treat as plain text (invalid format)
                print(f"Received invalid message format: {message[:100]}...")
                await send_error(
                    websocket,
                    "Please send messages in the proper format"
                )
            
    except WebSocketDisconnect:
        print(f"WebSocket connection closed (session: {session_id})")
    finally:
        # Clean up session
        remove_session(session_id)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print(f"Starting ERICAD Backend on http://{SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
