# Guarda historial + feedback en JSON (base para que luego PyTorch entrene con datos reales)

from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# carpeta raíz del proyecto
ROOT = Path(__file__).resolve().parents[1]     
# respeta carpeta "Data" 
DATA_DIR = ROOT / "Data"                        
HISTORY_FILE = DATA_DIR / "historial.json"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def _load_events() -> List[Dict[str, Any]]:
    _ensure_data_dir()

    if not HISTORY_FILE.exists():
        return []

    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:

        # Si se corrompe el JSON, lo respaldamos y empezamos limpio
        backup = HISTORY_FILE.with_suffix(".json.bak")
        HISTORY_FILE.replace(backup)
        return []


def _save_events(events: List[Dict[str, Any]]) -> None:
    _ensure_data_dir()
    HISTORY_FILE.write_text(
        json.dumps(events, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def save_run(respuestas: Dict[str, Any], result: Any) -> str:

    run_id = str(uuid.uuid4())

    events = _load_events()
    events.append({
        "type": "run",
        "run_id": run_id,
        "ts": _now_iso(),
        "respuestas": respuestas,
        "resultado": {
            "persona": getattr(result, "persona", ""),
            "score": getattr(result, "score", None),
            "resumen": getattr(result, "resumen", ""),
        }
    })
    _save_events(events)
    return run_id


def save_feedback(run_id: str, rating: int, comentario: str = "") -> None:
    events = _load_events()
    events.append({
        "type": "feedback",
        "run_id": run_id,
        "ts": _now_iso(),
        "rating": int(rating),
        "comentario": (comentario or "").strip()
    })
    _save_events(events)
