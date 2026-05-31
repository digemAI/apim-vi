from __future__ import annotations
from typing import Any, Dict, List, Tuple

# Zonas financieras/emocionales
ZONE_GREEN = "🟢"   # Control / estabilidad
ZONE_YELLOW = "🟡"  # Friccion / alerta
ZONE_RED = "🔴"     # Crisis / evento critico

# Tendencias (comparacion contra el pasado)
TREND_UP = "📈"     # Mejora
TREND_FLAT = "➖"   # Estable
TREND_DOWN = "📉"   # Empeora


# Palabras clave  
# Si aparece algo de aqui es rojo
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

# Señales de control o planeacion
GREEN_KEYWORDS = {
    "tranquilo", "tranquila", "controlado", "diversión", "diversion",
    "planeado", "planificado", "estacional", "enfocado", "bien"
}

# Traduce como te sentiste a una zona base
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

# Funciones Auxiliares
def _norm(s: str) -> str:

    # Limpia texto, es decir, quita espacios y pasa a minusculas
    return (s or "").strip().lower()

# Revisa si alguna palabra clave aparece en el texto
def _contains_any(text: str, keywords: set[str]) -> bool:
    t = _norm(text)
    return any(k in t for k in keywords)

# Convierte zona a numero para comparar
def _zone_rank(z: str) -> int:

    # rojo = 0 (peor), amarillo = 1, verde = 2 (mejor)
    return {ZONE_RED: 0, ZONE_YELLOW: 1, ZONE_GREEN: 2}.get(z, 1)

# Convierte número de vuelta a zona
def _rank_to_zone(r: int) -> str:
    return {0: ZONE_RED, 1: ZONE_YELLOW, 2: ZONE_GREEN}.get(r, ZONE_YELLOW)

# Zona de un evento usando emocion declarada, palabras clave en descripcion y contexto
def compute_zone(event: Dict[str, Any]) -> str:
    desc = _norm(event.get("description", ""))
    ctx = _norm(event.get("context", ""))
    amount = _norm(event.get("amount", ""))  # aún no pesa fuerte
    emo = _norm(event.get("emotion", ""))

    # 1) Prioridad absoluta: palabras rojas
    if _contains_any(desc, RED_KEYWORDS) or _contains_any(ctx, RED_KEYWORDS):
        return ZONE_RED

    # 2) Zona base por emocion
    if emo in EMOTION_TO_ZONE:
        base = EMOTION_TO_ZONE[emo]
    else:
        base = ZONE_YELLOW  # neutral si no sabemos

    # 3) Ajustes suaves por palabras amarillas o verdes
    if _contains_any(desc, YELLOW_KEYWORDS) or _contains_any(ctx, YELLOW_KEYWORDS):
        base = _rank_to_zone(min(_zone_rank(base), _zone_rank(ZONE_YELLOW)))

    if _contains_any(desc, GREEN_KEYWORDS) or _contains_any(ctx, GREEN_KEYWORDS):
        base = _rank_to_zone(max(_zone_rank(base), _zone_rank(ZONE_GREEN)))

    # 4) El monto aun no manda (MVP)
    return base

# Compara zona anterior vs actual para saber si mejora, empeora o sigue igual
def compute_trend(prev_zone: str | None, current_zone: str) -> str:
    if not prev_zone:
        return TREND_FLAT

    p = _zone_rank(prev_zone)
    c = _zone_rank(current_zone)

    if c > p:
        return TREND_UP
    if c < p:
        return TREND_DOWN
    return TREND_FLAT

#   Calcula zona y tendencia usando el ultimo evento registrado y la ultima zona guardada en memoria
def evaluate_zone_and_trend(memory: Dict[str, Any]) -> Tuple[str, str]:
    events: List[Dict[str, Any]] = memory.get("events", [])
    if not events:
        return ZONE_YELLOW, TREND_FLAT

    last_event = events[-1]
    current_zone = compute_zone(last_event)
    prev_zone = memory.get("last_zone")
    trend = compute_trend(prev_zone, current_zone)

    return current_zone, trend

# El modo contencion no cambia la zona, solo el tono y la recomendacion
def build_feedback(
    memory: Dict[str, Any],
    zone: str,
    trend: str,
) -> Dict[str, str]:
    contencion = bool(memory.get("settings", {}).get("mode_contencion", False))

    # Comentario base segun zona
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

    # Sugerencia cambia segun contencion
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
