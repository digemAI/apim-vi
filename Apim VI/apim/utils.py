# apim/utils.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List


def clamp_int(value: Any, min_v: int, max_v: int, default: int) -> int:
    """Convierte a int y limita el rango. Si falla, regresa default."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, v))


def clamp_float(value: Any, min_v: float, max_v: float, default: float) -> float:
    """Convierte a float y limita el rango. Si falla, regresa default."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, v))


def format_mxn(amount: float) -> str:
    """Formatea cantidad como MXN con separador de miles."""
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        amt = 0.0
    return f"${amt:,.0f} MXN"


def ensure_data_dir(project_root: Path) -> Path:
    """Asegura que exista la carpeta data/ y la regresa."""
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def history_path(project_root: Path) -> Path:
    """Ruta del historial JSON (archivo que NO conviene subir a Git)."""
    return ensure_data_dir(project_root) / "history.json"


def load_history(project_root: Path) -> List[Dict[str, Any]]:
    path = history_path(project_root)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        # Si se corrompe, no tumbamos la app
        return []


def append_history(project_root: Path, record: Dict[str, Any]) -> None:
    """Agrega un registro al historial en data/history.json."""
    history = load_history(project_root)
    record = dict(record)
    record["timestamp"] = datetime.now().isoformat(timespec="seconds")
    history.append(record)
    history_path(project_root).write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
