from __future__ import annotations
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Ubicacion del proyecto
def _project_root() -> Path:
    """
    Detecta la raiz del proyecto.
    """
    # __file__ es la ruta de este archivo, parents[1] sube dos niveles hasta la raiz del repo
    return Path(__file__).resolve().parents[1]

# Carpeta datos
def _data_dir() -> Path:

    # Apunta a la carpeta /data
    d = _project_root() / "data"

    # Si no existe, la crea automaticamente
    d.mkdir(parents=True, exist_ok=True)

    return d

# Ruta del archivo de memoria
def _memory_path() -> Path:

    # data/apim_memory.json
    return _data_dir() / "apim_memory.json"


# Primer uso de la memoria base 
def _default_memory() -> Dict[str, Any]:

    # Estructura inicial del cerebro de APIM VI
    return {
        "user": {
            "profile": None,              
            "secondary_profile": None,    
        },
        "settings": {
            "window": "weekly",           
            "mode_contencion": False,     
        },
        "events": [],                   
        "weekly_snapshots": [],          
        "last_zone": None,              
        "last_trend": None,              
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "schema_version": 1,             
    }


# Serializador
def _json_safe(obj: Any) -> Any:
    """
    Convierte objetos no compatibles con JSON
    a algo que sí se pueda guardar.
    """

    # Si es una dataclass → dict
    if is_dataclass(obj):
        return asdict(obj)

    # Si es una ruta → string
    if isinstance(obj, (Path,)):
        return str(obj)

    # Si tiene isoformat (datetime) → string
    if hasattr(obj, "isoformat"):
        try:
            return obj.isoformat()
        except Exception:
            pass

    return obj


# Cargar memoria
def load_memory() -> Dict[str, Any]:
    """
    Carga la memoria desde data/apim_memory.json.
    Si no existe (primer uso), la crea automaticamente.
    """
    path = _memory_path()

    # Primer uso: no existe el archivo
    if not path.exists():
        memory = _default_memory()
        save_memory(memory)
        return memory

    # Intentamos leer el archivo
    try:
        with path.open("r", encoding="utf-8") as f:
            memory = json.load(f)

    # Si el json está corrupto
    except json.JSONDecodeError:

        # Se respalda el archivo roto
        backup = path.with_suffix(".corrupt.backup.json")
        path.rename(backup)

        # Se crea una memoria nueva
        memory = _default_memory()
        save_memory(memory)
        return memory

    # Si faltan llaves (compatibilidad futura)
    memory = _ensure_schema(memory)
    return memory

# Guardar memoria
def save_memory(memory: Dict[str, Any]) -> None:
    path = _memory_path()

    # Actualiza fecha de modificacion
    memory["updated_at"] = datetime.now().isoformat()

    # Asegura estructura completa
    memory = _ensure_schema(memory)

    # Escribe el archivo json
    with path.open("w", encoding="utf-8") as f:
        json.dump(
            memory,
            f,
            ensure_ascii=False,
            indent=2,
            default=_json_safe
        )

# Si el json viene incompleto, rellena lo que falte sin borrar datos existentes.
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


# Agregar un evento a la memoria
def add_event(memory: Dict[str, Any], event: Dict[str, Any]) -> None:
    e = dict(event)

    # Valores por defecto si faltan
    e.setdefault("timestamp", datetime.now().isoformat())
    e.setdefault("date", "")
    e.setdefault("description", "")
    e.setdefault("amount", "")
    e.setdefault("context", "")
    e.setdefault("emotion", "")

    memory.setdefault("events", [])
    memory["events"].append(e)


# Borra todos los eventos, solo para pruebas.
def clear_events(memory: Dict[str, Any]) -> None:
    memory["events"] = []

# Devuelve copia de los eventos
def get_events(memory: Dict[str, Any]) -> list[Dict[str, Any]]:
    return list(memory.get("events", []))
