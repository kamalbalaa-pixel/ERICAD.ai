"""
ERICAD Utilities
Helper functions for the backend.
"""

import json
from typing import Any, Optional
from fastapi import WebSocket


def get_field(data: dict, *keys, default: Any = None) -> Any:
    """
    Get a field from a dictionary with case-insensitive key matching.
    Tries each key in order until one is found.
    
    Args:
        data: The dictionary to search.
        *keys: Keys to try (e.g., "type", "Type").
        default: Default value if no key is found.
        
    Returns:
        The value found or the default.
    """
    for key in keys:
        if key in data:
            return data[key]
    return default


def get_string_field(data: dict, *keys, default: str = "") -> str:
    """Get a string field with case-insensitive matching."""
    value = get_field(data, *keys, default=default)
    return str(value) if value is not None else default


def get_bool_field(data: dict, *keys, default: bool = False) -> bool:
    """Get a boolean field with case-insensitive matching."""
    value = get_field(data, *keys, default=default)
    return bool(value) if value is not None else default


def get_int_field(data: dict, *keys, default: int = 0) -> int:
    """Get an integer field with case-insensitive matching."""
    value = get_field(data, *keys, default=default)
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def get_list_field(data: dict, *keys, default: Optional[list] = None) -> list:
    """Get a list field with case-insensitive matching."""
    value = get_field(data, *keys, default=default)
    return value if isinstance(value, list) else (default or [])


async def send_response(websocket: WebSocket, msg_type: str, message: str) -> None:
    """Send a JSON response to the WebSocket client."""
    await websocket.send_text(json.dumps({
        "type": msg_type,
        "message": message
    }))


async def send_error(websocket: WebSocket, message: str) -> None:
    """Send an error response to the WebSocket client."""
    await send_response(websocket, "error", message)


async def send_thinking(websocket: WebSocket, message: str) -> None:
    """Send a thinking indicator to the WebSocket client."""
    await send_response(websocket, "thinking", message)

