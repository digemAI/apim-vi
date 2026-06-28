from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# project root folder
ROOT = Path(__file__).resolve().parents[1]

# uses the existing "Data" folder
DATA_DIR = ROOT / "Data"
HISTORY_FILE = DATA_DIR / "history.json"

# Returns the current date and time
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# Ensures the folder exists
def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

# Returns an empty list if the file doesn't exist. If the JSON is corrupted, creates a backup and resets.
def _load_events() -> List[Dict[str, Any]]:
    _ensure_data_dir()

    if not HISTORY_FILE.exists():
        return []

    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:

        # If the JSON is corrupted, back it up and start fresh
        backup = HISTORY_FILE.with_suffix(".json.bak")
        HISTORY_FILE.replace(backup)
        return []

# Saves the full list of events to history.json.
def _save_events(events: List[Dict[str, Any]]) -> None:
    _ensure_data_dir()
    HISTORY_FILE.write_text(
        json.dumps(events, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# Saves a system run: the user's answers, classified profile, score, and result summary
def save_run(answers: Dict[str, Any], result: Any) -> str:

    run_id = str(uuid.uuid4())

    events = _load_events()
    events.append({
        "type": "run",
        "run_id": run_id,
        "ts": _now_iso(),
        "answers": answers,
        "result": {
            "profile": getattr(result, "profile", ""),
            "score": getattr(result, "score", None),
            "summary": getattr(result, "summary", ""),
        }
    })
    _save_events(events)
    return run_id

# Saves user feedback (numeric rating, optional free text)
def save_feedback(run_id: str, rating: int, comment: str = "") -> None:
    events = _load_events()
    events.append({
        "type": "feedback",
        "run_id": run_id,
        "ts": _now_iso(),
        "rating": int(rating),
        "comment": (comment or "").strip()
    })
    _save_events(events)

# V3
# shadow = parallel logging of the V3 model

def save_shadow(run_id: str, v3_pred: Dict[str, Any], v2_profile: Optional[str] = None) -> None:
    events = _load_events()
    event = {
        "type": "shadow",
        "run_id": run_id,
        "ts": _now_iso(),
        "v3": v3_pred,
    }
    if v2_profile is not None:
        event["v2_profile"] = v2_profile

    events.append(event)
    _save_events(events)
