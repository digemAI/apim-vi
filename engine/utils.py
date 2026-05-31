from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

# Convierte un valor a int y lo limita a un rango si la conversión falla, devuelve el valor por defecto.
def clamp_int(value: Any, min_v: int, max_v: int, default: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, v))

# Convierte un valor a float y lo limita a un rango si la conversión falla, devuelve el valor por defecto.
def clamp_float(value: Any, min_v: float, max_v: float, default: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, v))

# Formatea cantidad como MXN con separador de miles y sin decimales
def format_mxn(amount: float) -> str: 
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        amt = 0.0
    return f"${amt:,.0f} MXN"

#  Asegura que exista la carpeta data/ dentro del proyecto, si no existe, la crea. 
def ensure_data_dir(project_root: Path) -> Path:
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

# Devuelve la ruta completa al archivo data/history.json.
def history_path(project_root: Path) -> Path:
    return ensure_data_dir(project_root) / "history.json"

# Carga el historial desde data/history.json.  Si el archivo no existe o esta corrupto,  devuelve una lista vacia 
def load_history(project_root: Path) -> List[Dict[str, Any]]:
    path = history_path(project_root)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

# Agrega un nuevo registro al historial en data/history.json.
    history = load_history(project_root)
def append_history(project_root: Path, record: Dict[str, Any]) -> None:
    history = load_history(project_root)
    record = dict(record)
    record["timestamp"] = datetime.now().isoformat(timespec="seconds")
    history.append(record)
    history_path(project_root).write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
