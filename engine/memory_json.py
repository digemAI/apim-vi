from __future__ import annotations
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Project location
def _project_root() -> Path:
    """
    Detects the project root.
    """
    # __file__ is this file's path; parents[1] goes up two levels to the repo root
    return Path(__file__).resolve().parents[1]

# Data folder
def _data_dir() -> Path:

    # Points to the Data folder
    d = _project_root() / "Data"

    # Creates it automatically if missing
    d.mkdir(parents=True, exist_ok=True)

    return d

# Path to the memory file
def _memory_path() -> Path:

    # Data/memory.json
    return _data_dir() / "memory.json"


# First-time default memory
def _default_memory() -> Dict[str, Any]:

    # Initial structure of APIM VI's brain
    return {
        "user": {
            "profile": None,
            "secondary_profile": None,
        },
        "settings": {
            "window": "weekly",
            "containment_mode": False,
        },
        "events": [],
        "weekly_snapshots": [],
        "last_zone": None,
        "last_trend": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "schema_version": 1,
    }


# Serializer
def _json_safe(obj: Any) -> Any:
    """
    Converts objects that aren't JSON-compatible
    into something that can be saved.
    """

    # If it's a dataclass → dict
    if is_dataclass(obj):
        return asdict(obj)

    # If it's a Path → string
    if isinstance(obj, (Path,)):
        return str(obj)

    # If it has isoformat (datetime) → string
    if hasattr(obj, "isoformat"):
        try:
            return obj.isoformat()
        except Exception:
            pass

    return obj


# Load memory
def load_memory() -> Dict[str, Any]:
    """
    Loads memory from Data/memory.json.
    Creates it automatically on first use if missing.
    """
    path = _memory_path()

    # First use: file doesn't exist
    if not path.exists():
        memory = _default_memory()
        save_memory(memory)
        return memory

    # Try to read the file
    try:
        with path.open("r", encoding="utf-8") as f:
            memory = json.load(f)

    # If the JSON is corrupted
    except json.JSONDecodeError:

        # Back up the broken file
        backup = path.with_suffix(".corrupt.backup.json")
        path.rename(backup)

        # Create a fresh memory
        memory = _default_memory()
        save_memory(memory)
        return memory

    # Fill in missing keys (forward compatibility)
    memory = _ensure_schema(memory)
    return memory

# Save memory
def save_memory(memory: Dict[str, Any]) -> None:
    path = _memory_path()

    # Update modification timestamp
    memory["updated_at"] = datetime.now().isoformat()

    # Ensure the structure is complete
    memory = _ensure_schema(memory)

    # Write the JSON file
    with path.open("w", encoding="utf-8") as f:
        json.dump(
            memory,
            f,
            ensure_ascii=False,
            indent=2,
            default=_json_safe
        )

# If the JSON is incomplete, fill in what's missing without deleting existing data.
def _ensure_schema(memory: Dict[str, Any]) -> Dict[str, Any]:
    base = _default_memory()

    def merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in src.items():
            if k not in dst:
                dst[k] = v
            else:
                if isinstance(v, dict) and isinstance(dst[k], dict):
                    dst[k] = merge(dst[k], v)
        return dst

    return merge(memory, base)


# Add an event to memory
def add_event(memory: Dict[str, Any], event: Dict[str, Any]) -> None:
    e = dict(event)

    # Default values if missing
    e.setdefault("timestamp", datetime.now().isoformat())
    e.setdefault("date", "")
    e.setdefault("description", "")
    e.setdefault("amount", "")
    e.setdefault("context", "")
    e.setdefault("emotion", "")

    memory.setdefault("events", [])
    memory["events"].append(e)


# Clears all events, for testing only.
def clear_events(memory: Dict[str, Any]) -> None:
    memory["events"] = []

# Returns a copy of the events
def get_events(memory: Dict[str, Any]) -> list[Dict[str, Any]]:
    return list(memory.get("events", []))
