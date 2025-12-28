# Permite anotaciones modernas de tipos
from __future__ import annotations

# Para timestamps de los snapshots
from datetime import datetime

# Tipos para claridad
from typing import Any, Dict, List, Tuple

# Importamos la lógica (NO guardamos aquí)
from apim_vi.rules import (
    compute_zone,
    compute_trend,
    build_feedback,
    ZONE_GREEN,
    ZONE_YELLOW,
    ZONE_RED,
)


# =========================
# FUNCIONES AUXILIARES
# =========================
def _norm(s: str) -> str:
    # Limpia texto (evita None y espacios)
    return (s or "").strip()


def _safe_get(d: Dict[str, Any], key: str, default: str = "") -> str:
    # Obtiene un valor del dict y lo normaliza
    v = d.get(key, default)
    return _norm(str(v))


# =========================
# SELECCIÓN DE EVENTOS
# =========================
def _last_n_events(memory: Dict[str, Any], n: int = 5) -> List[Dict[str, Any]]:
    # Toma los últimos N eventos de la memoria
    events = memory.get("events", [])
    if not events:
        return []
    return events[-n:]


# =========================
# CONSTRUCCIÓN DE FILAS
# =========================
def _make_rows(events: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convierte eventos crudos en filas reportables:
    Fecha | Evento | Monto | Contexto | Emoción | Zona | Tendencia
    """
    rows: List[Dict[str, str]] = []
    prev_zone = None

    for e in events:
        # Zona por evento
        z = compute_zone(e)

        # Tendencia dentro del reporte (comparando evento anterior)
        t = compute_trend(prev_zone, z) if prev_zone else "➖"

        rows.append({
            "date": _safe_get(e, "date"),
            "event": _safe_get(e, "description"),
            "amount": _safe_get(e, "amount"),
            "context": _safe_get(e, "context"),
            "emotion": _safe_get(e, "emotion"),
            "zone": z,
            "trend": t,
        })

        prev_zone = z

    return rows


# =========================
# CONTEO DE ZONAS
# =========================
def _zone_counts(rows: List[Dict[str, str]]) -> Tuple[int, int, int]:
    # Cuenta cuántos eventos cayeron en cada zona
    g = sum(1 for r in rows if r["zone"] == ZONE_GREEN)
    y = sum(1 for r in rows if r["zone"] == ZONE_YELLOW)
    r = sum(1 for r in rows if r["zone"] == ZONE_RED)
    return g, y, r


# =========================
# ZONA GLOBAL SEMANAL
# =========================
def _overall_zone(rows: List[Dict[str, str]]) -> str:
    """
    Regla MVP para zona global semanal:
    - ≥2 rojos → 🔴
    - 1 rojo → 🟡 (hubo evento crítico)
    - ≥2 amarillos → 🟡
    - resto → 🟢
    """
    g, y, r = _zone_counts(rows)

    if r >= 2:
        return ZONE_RED
    if r == 1:
        return ZONE_YELLOW
    if y >= 2:
        return ZONE_YELLOW
    return ZONE_GREEN


# =========================
# TENDENCIA GLOBAL
# =========================
def _overall_trend(memory: Dict[str, Any], overall_zone: str) -> str:
    """
    Compara la zona global actual contra:
    - el último snapshot semanal si existe
    - si no, contra memory["last_zone"]
    """
    prev_zone = None

    snaps = memory.get("weekly_snapshots", [])
    if snaps:
        prev_zone = snaps[-1].get("overall_zone")

    if not prev_zone:
        prev_zone = memory.get("last_zone")

    return compute_trend(prev_zone, overall_zone)


# =========================
# IMPRESIÓN DE TABLA
# =========================
def _print_table(rows: List[Dict[str, str]]) -> None:
    # Encabezados y anchos fijos (CLI friendly)
    headers = ["Fecha", "Evento", "Monto", "Contexto", "Emoción", "Zona", "Tend."]
    col_widths = [10, 24, 10, 18, 12, 4, 5]

    # Corta texto largo para que no rompa la tabla
    def cut(text: str, width: int) -> str:
        t = (text or "")
        if len(t) <= width:
            return t.ljust(width)
        return (t[: width - 1] + "…").ljust(width)

    # Línea de encabezado
    line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    sep = "-+-".join("-" * w for w in col_widths)

    print("\n" + line)
    print(sep)

    # Filas
    for r in rows:
        print(" | ".join([
            cut(r["date"], col_widths[0]),
            cut(r["event"], col_widths[1]),
            cut(r["amount"], col_widths[2]),
            cut(r["context"], col_widths[3]),
            cut(r["emotion"], col_widths[4]),
            cut(r["zone"], col_widths[5]),
            cut(r["trend"], col_widths[6]),
        ]))


# =========================
# REPORTE SEMANAL (API)
# =========================
def weekly_report(
    memory: Dict[str, Any],
    n_events: int = 5,
    save_snapshot: bool = True
) -> Dict[str, Any]:
    """
    Genera el reporte semanal:
    - usa los últimos N eventos
    - imprime tabla + resumen
    - guarda snapshot si se pide
    """
    events = _last_n_events(memory, n=n_events)
    if not events:
        print("\n📊 APIM VI — Reporte semanal")
        print("No hay eventos registrados aún.")
        return {"ok": False, "reason": "no_events"}

    # Construimos filas y mostramos tabla
    rows = _make_rows(events)
    _print_table(rows)

    # Zona y tendencia global
    overall_zone = _overall_zone(rows)
    overall_trend = _overall_trend(memory, overall_zone)

    # Texto humano (depende de modo contención)
    fb = build_feedback(memory, overall_zone, overall_trend)

    # Conteos
    g, y, r = _zone_counts(rows)

    # Resumen final
    print("\n📌 Resumen semanal")
    print(f"- Eventos analizados: {len(rows)}")
    print(f"- Conteo zonas: 🟢{g}  🟡{y}  🔴{r}")
    print(f"- Zona global: {overall_zone}")
    print(f"- Tendencia: {overall_trend}")
    print(f"- Insight: {fb['comment']}")
    print(f"- Sugerencia: {fb['suggestion']}")

    # Snapshot que se guarda en memoria
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "n_events": len(rows),
        "overall_zone": overall_zone,
        "overall_trend": overall_trend,
        "counts": {"green": g, "yellow": y, "red": r},
        "insight": fb["comment"],
        "suggestion": fb["suggestion"],
    }

    if save_snapshot:
        memory.setdefault("weekly_snapshots", [])
        memory["weekly_snapshots"].append(snapshot)

    return {"ok": True, "snapshot": snapshot}
