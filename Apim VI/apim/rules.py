# Permite usar anotaciones modernas de tipos
from __future__ import annotations

# Tipos para claridad (no afectan ejecución)
from typing import Any, Dict, List, Tuple


# =========================
# DEFINICIÓN DE ESTADOS
# =========================

# Zonas financieras/emocionales
ZONE_GREEN = "🟢"   # Control / estabilidad
ZONE_YELLOW = "🟡"  # Fricción / alerta
ZONE_RED = "🔴"     # Crisis / evento crítico

# Tendencias (comparación contra el pasado)
TREND_UP = "📈"     # Mejora
TREND_FLAT = "➖"   # Estable
TREND_DOWN = "📉"   # Empeora


# =========================
# PALABRAS CLAVE (HEURÍSTICAS)
# =========================
# Si aparece algo de aquí → casi seguro es rojo
RED_KEYWORDS = {
    "robo", "despido", "renuncia", "divorcio", "demanda", "fraude",
    "choque", "accidente", "hospital", "cirugía", "urgente", "deuda",
    "no puedo pagar", "mínimo", "embargo", "crisis"
}

# Señales de alerta, pero no crisis total
YELLOW_KEYWORDS = {
    "estrés", "estres", "incertidumbre", "ajuste", "apretado",
    "imprevisto", "retraso", "tensión", "preocupación", "preocupacion"
}

# Señales de control o planeación
GREEN_KEYWORDS = {
    "tranquilo", "tranquila", "controlado", "diversión", "diversion",
    "planeado", "planificado", "estacional", "enfocado", "bien"
}


# =========================
# MAPA EMOCIÓN → ZONA
# =========================
# Traduce cómo te sentiste a una zona base
EMOTION_TO_ZONE = {
    # verde
    "tranquilo": ZONE_GREEN,
    "tranquila": ZONE_GREEN,
    "diversión": ZONE_GREEN,
    "diversion": ZONE_GREEN,
    "satisfacción": ZONE_GREEN,
    "satisfaccion": ZONE_GREEN,
    "en paz": ZONE_GREEN,
    "enfocado": ZONE_GREEN,

    # amarilla
    "estrés": ZONE_YELLOW,
    "estres": ZONE_YELLOW,
    "preocupación": ZONE_YELLOW,
    "preocupacion": ZONE_YELLOW,
    "ansiedad": ZONE_YELLOW,
    "tensión": ZONE_YELLOW,
    "tension": ZONE_YELLOW,

    # roja
    "pánico": ZONE_RED,
    "panico": ZONE_RED,
    "enojo": ZONE_RED,
    "miedo": ZONE_RED,
    "culpa": ZONE_RED,
    "conflictivo": ZONE_RED,
    "desesperación": ZONE_RED,
    "desesperacion": ZONE_RED,
}


# =========================
# FUNCIONES AUXILIARES
# =========================
def _norm(s: str) -> str:
    # Limpia texto: quita espacios y pasa a minúsculas
    return (s or "").strip().lower()


def _contains_any(text: str, keywords: set[str]) -> bool:
    # Revisa si alguna palabra clave aparece en el texto
    t = _norm(text)
    return any(k in t for k in keywords)


def _zone_rank(z: str) -> int:
    # Convierte zona a número para comparar
    # rojo = 0 (peor), amarillo = 1, verde = 2 (mejor)
    return {ZONE_RED: 0, ZONE_YELLOW: 1, ZONE_GREEN: 2}.get(z, 1)


def _rank_to_zone(r: int) -> str:
    # Convierte número de vuelta a zona
    return {0: ZONE_RED, 1: ZONE_YELLOW, 2: ZONE_GREEN}.get(r, ZONE_YELLOW)


# =========================
# CÁLCULO DE ZONA
# =========================
def compute_zone(event: Dict[str, Any]) -> str:
    """
    Decide la zona de un evento usando:
    - emoción declarada
    - palabras clave en descripción y contexto

    Regla clave:
    👉 si algo huele a rojo, manda rojo.
    """
    desc = _norm(event.get("description", ""))
    ctx = _norm(event.get("context", ""))
    amount = _norm(event.get("amount", ""))  # aún no pesa fuerte
    emo = _norm(event.get("emotion", ""))

    # 1) Prioridad absoluta: palabras rojas
    if _contains_any(desc, RED_KEYWORDS) or _contains_any(ctx, RED_KEYWORDS):
        return ZONE_RED

    # 2) Zona base por emoción
    if emo in EMOTION_TO_ZONE:
        base = EMOTION_TO_ZONE[emo]
    else:
        base = ZONE_YELLOW  # neutral si no sabemos

    # 3) Ajustes suaves por palabras amarillas o verdes
    if _contains_any(desc, YELLOW_KEYWORDS) or _contains_any(ctx, YELLOW_KEYWORDS):
        base = _rank_to_zone(min(_zone_rank(base), _zone_rank(ZONE_YELLOW)))

    if _contains_any(desc, GREEN_KEYWORDS) or _contains_any(ctx, GREEN_KEYWORDS):
        base = _rank_to_zone(max(_zone_rank(base), _zone_rank(ZONE_GREEN)))

    # 4) El monto aún no manda (MVP)
    return base


# =========================
# CÁLCULO DE TENDENCIA
# =========================
def compute_trend(prev_zone: str | None, current_zone: str) -> str:
    """
    Compara zona anterior vs actual:
    - Mejora → 📈
    - Empeora → 📉
    - Igual → ➖
    """
    if not prev_zone:
        return TREND_FLAT

    p = _zone_rank(prev_zone)
    c = _zone_rank(current_zone)

    if c > p:
        return TREND_UP
    if c < p:
        return TREND_DOWN
    return TREND_FLAT


# =========================
# ZONA + TENDENCIA (PUENTE)
# =========================
def evaluate_zone_and_trend(memory: Dict[str, Any]) -> Tuple[str, str]:
    """
    Calcula zona y tendencia usando:
    - el último evento registrado
    - la última zona guardada en memoria

    Nota: aquí NO se guarda nada.
    main.py decide cuándo persistir.
    """
    events: List[Dict[str, Any]] = memory.get("events", [])
    if not events:
        return ZONE_YELLOW, TREND_FLAT

    last_event = events[-1]
    current_zone = compute_zone(last_event)
    prev_zone = memory.get("last_zone")
    trend = compute_trend(prev_zone, current_zone)

    return current_zone, trend


# =========================
# MODO CONTENCIÓN (TONO)
# =========================
def build_feedback(
    memory: Dict[str, Any],
    zone: str,
    trend: str,
) -> Dict[str, str]:
    """
    Genera texto humano:
    - comment: diagnóstico corto
    - suggestion: siguiente paso sugerido

    El modo contención NO cambia la zona,
    solo cambia el tono y la recomendación.
    """
    contencion = bool(memory.get("settings", {}).get("mode_contencion", False))

    # Comentario base según zona
    if zone == ZONE_GREEN:
        comment = "Se ve control y claridad en la decisión."
    elif zone == ZONE_YELLOW:
        comment = "Hay fricción; conviene priorizar estabilidad antes de optimizar."
    else:
        comment = "Evento crítico: primero contención y continuidad."

    # Ajuste por tendencia
    if trend == TREND_UP:
        comment += " La recuperación va mejor."
    elif trend == TREND_DOWN:
        comment += " La presión subió; mejor bajar fricción."
    else:
        comment += " Mantén el sistema simple."

    # Sugerencia cambia según contención
    if contencion:
        if zone == ZONE_RED:
            suggestion = "¿Lo pausamos 48h y definimos solo qué cubrir primero?"
        elif zone == ZONE_YELLOW:
            suggestion = "¿Quieres activar reglas mínimas de caja por 7 días?"
        else:
            suggestion = "¿Marcamos esto como ‘planeado’ para no distorsionar el mes?"
    else:
        if zone == ZONE_RED:
            suggestion = "¿Quieres que prioricemos un plan de continuidad (lo urgente primero)?"
        elif zone == ZONE_YELLOW:
            suggestion = "¿Te armo 2 opciones rápidas: recorte suave vs recorte fuerte?"
        else:
            suggestion = "¿Lo marcamos como ‘estacional’ o ‘prioritario’ para reportes?"

    return {"comment": comment, "suggestion": suggestion}
