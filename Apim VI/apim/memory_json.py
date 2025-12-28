# Permite usar anotaciones de tipos modernas (no afecta ejecución)
from __future__ import annotations

# Librería estándar para trabajar con archivos JSON
import json

# Utilidades para convertir dataclasses a diccionarios
from dataclasses import asdict, is_dataclass

# Para manejar fechas y horas
from datetime import datetime

# Para manejar rutas de archivos de forma segura
from pathlib import Path

# Tipos genéricos (solo para claridad)
from typing import Any, Dict


# =========================
# UBICACIÓN DEL PROYECTO
# =========================
def _project_root() -> Path:
    """
    Detecta la raíz del proyecto.
    Espera esta estructura:

      apim-vi/
        apim_vi/  <- este archivo vive aquí
        data/
    """
    # __file__ es la ruta de este archivo
    # parents[1] sube dos niveles hasta la raíz del repo
    return Path(__file__).resolve().parents[1]


# =========================
# CARPETA DE DATOS
# =========================
def _data_dir() -> Path:
    # Apunta a la carpeta /data
    d = _project_root() / "data"

    # Si no existe, la crea automáticamente
    d.mkdir(parents=True, exist_ok=True)

    return d


# =========================
# RUTA DEL ARCHIVO DE MEMORIA
# =========================
def _memory_path() -> Path:
    # data/apim_memory.json
    return _data_dir() / "apim_memory.json"


# =========================
# MEMORIA BASE (PRIMER USO)
# =========================
def _default_memory() -> Dict[str, Any]:
    # Esta es la estructura inicial del "cerebro" de APIM VI
    return {
        "user": {
            "profile": None,              # perfil principal (ej. jefe de jefes)
            "secondary_profile": None,    # opcional
        },
        "settings": {
            "window": "weekly",           # ventana de análisis
            "mode_contencion": False,     # modo contención ON / OFF
        },
        "events": [],                    # eventos registrados
        "weekly_snapshots": [],          # cierres semanales
        "last_zone": None,               # última zona 🟢🟡🔴
        "last_trend": None,              # última tendencia 📈➖📉
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "schema_version": 1,             # versión del esquema
    }


# =========================
# SERIALIZADOR SEGURO
# =========================
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


# =========================
# CARGAR MEMORIA
# =========================
def load_memory() -> Dict[str, Any]:
    """
    Carga la memoria desde data/apim_memory.json.
    Si no existe (primer uso), la crea automáticamente.
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

    # Si el JSON está corrupto
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


# =========================
# GUARDAR MEMORIA
# =========================
def save_memory(memory: Dict[str, Any]) -> None:
    """
    Guarda la memoria en JSON legible.
    """
    path = _memory_path()

    # Actualiza fecha de modificación
    memory["updated_at"] = datetime.now().isoformat()

    # Asegura estructura completa
    memory = _ensure_schema(memory)

    # Escribe el archivo JSON
    with path.open("w", encoding="utf-8") as f:
        json.dump(
            memory,
            f,
            ensure_ascii=False,
            indent=2,
            default=_json_safe
        )


# =========================
# ASEGURAR ESQUEMA
# =========================
def _ensure_schema(memory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Si el JSON viene incompleto, rellena
    lo que falte sin borrar datos existentes.
    """
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


# =========================
# AGREGAR EVENTO
# =========================
def add_event(memory: Dict[str, Any], event: Dict[str, Any]) -> None:
    """
    Agrega un evento a la memoria.
    Normaliza campos mínimos.
    """
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


# =========================
# UTILIDADES (PRUEBAS)
# =========================
def clear_events(memory: Dict[str, Any]) -> None:
    """
    Borra todos los eventos.
    Solo para pruebas.
    """
    memory["events"] = []


def get_events(memory: Dict[str, Any]) -> list[Dict[str, Any]]:
    # Devuelve copia de los eventos
    return list(memory.get("events", []))
