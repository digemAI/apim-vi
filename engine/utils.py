from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

# Converts a value to int and clamps it to a range; falls back to the default if conversion fails.
def clamp_int(value: Any, min_v: int, max_v: int, default: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, v))

# Converts a value to float and clamps it to a range; falls back to the default if conversion fails.
def clamp_float(value: Any, min_v: float, max_v: float, default: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, v))

# Formats an amount as MXN with thousands separators and no decimals
def format_mxn(amount: float) -> str:
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        amt = 0.0
    return f"${amt:,.0f} MXN"

# Ensures the Data/ folder exists inside the project; creates it if missing.
def ensure_data_dir(project_root: Path) -> Path:
    data_dir = project_root / "Data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

# Returns the full path to the Data/history.json file.
def history_path(project_root: Path) -> Path:
    return ensure_data_dir(project_root) / "history.json"

# Loads history from Data/history.json. Returns an empty list if the file doesn't exist or is corrupted.
def load_history(project_root: Path) -> List[Dict[str, Any]]:
    path = history_path(project_root)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

# Adds a new record to history in Data/history.json.
def append_history(project_root: Path, record: Dict[str, Any]) -> None:
    history = load_history(project_root)
    record = dict(record)
    record["timestamp"] = datetime.now().isoformat(timespec="seconds")
    history.append(record)
    history_path(project_root).write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
