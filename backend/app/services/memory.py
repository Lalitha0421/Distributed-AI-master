"""
memory.py — JSON-backed persistent conversation memory.
Stores chat history in 'chat_history.json' so it survives server reloads.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

from app.core.logger import logger

_MEMORY_FILE = "chat_history.json"
_MAX_MESSAGES: int = 20  # Increased for better "past task" review

def _load_memory() -> Dict[str, List[dict]]:
    if not os.path.exists(_MEMORY_FILE):
        return {}
    try:
        with open(_MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error(f"Failed to load memory file: {exc}")
        return {}

def _save_memory(memory: Dict[str, List[dict]]) -> None:
    try:
        with open(_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2)
    except Exception as exc:
        logger.error(f"Failed to save memory file: {exc}")

def add_message(session_id: str, role: str, content: str) -> None:
    memory = _load_memory()
    if session_id not in memory:
        memory[session_id] = []
    
    memory[session_id].append({"role": role, "content": content})
    
    if len(memory[session_id]) > _MAX_MESSAGES:
        memory[session_id] = memory[session_id][-_MAX_MESSAGES:]
    
    _save_memory(memory)
    logger.debug(f"Memory [{session_id}]: saved '{role}' message")

def get_history(session_id: str) -> List[dict]:
    memory = _load_memory()
    return memory.get(session_id, [])

def clear_session(session_id: str) -> None:
    memory = _load_memory()
    if session_id in memory:
        memory.pop(session_id)
        _save_memory(memory)
        logger.info(f"Memory [{session_id}]: cleared")