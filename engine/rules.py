from __future__ import annotations
from typing import Any, Dict, List, Tuple

# Financial/emotional zones
ZONE_GREEN = "🟢"   # Control / stability
ZONE_YELLOW = "🟡"  # Friction / alert
ZONE_RED = "🔴"     # Crisis / critical event

# Trends (comparison against the past)
TREND_UP = "📈"     # Improves
TREND_FLAT = "➖"   # Stable
TREND_DOWN = "📉"   # Worsens


# Keywords
# If any of these appear, it's red
RED_KEYWORDS = {
    "theft", "stolen", "layoff", "fired", "resignation", "divorce", "lawsuit",
    "fraud", "crash", "accident", "hospital", "surgery", "urgent", "debt",
    "can't pay", "minimum payment", "repossession", "crisis"
}

# Warning signals, but not a full crisis
YELLOW_KEYWORDS = {
    "stress", "uncertainty", "adjustment", "tight",
    "unexpected", "delay", "tension", "worry", "worried"
}

# Signals of control or planning
GREEN_KEYWORDS = {
    "calm", "under control", "fun",
    "planned", "seasonal", "focused", "good"
}

# Maps how you felt to a base zone
EMOTION_TO_ZONE = {
    # green
    "calm": ZONE_GREEN,
    "fun": ZONE_GREEN,
    "satisfaction": ZONE_GREEN,
    "at peace": ZONE_GREEN,
    "focused": ZONE_GREEN,

    # yellow
    "stress": ZONE_YELLOW,
    "worried": ZONE_YELLOW,
    "anxiety": ZONE_YELLOW,
    "tension": ZONE_YELLOW,

    # red
    "panic": ZONE_RED,
    "anger": ZONE_RED,
    "fear": ZONE_RED,
    "guilt": ZONE_RED,
    "conflicted": ZONE_RED,
    "despair": ZONE_RED,
}

# Helper functions
def _norm(s: str) -> str:

    # Cleans text: strips whitespace and lowercases it
    return (s or "").strip().lower()

# Checks whether any keyword appears in the text
def _contains_any(text: str, keywords: set[str]) -> bool:
    t = _norm(text)
    return any(k in t for k in keywords)

# Converts zone to a number for comparison
def _zone_rank(z: str) -> int:

    # red = 0 (worst), yellow = 1, green = 2 (best)
    return {ZONE_RED: 0, ZONE_YELLOW: 1, ZONE_GREEN: 2}.get(z, 1)

# Converts the number back to a zone
def _rank_to_zone(r: int) -> str:
    return {0: ZONE_RED, 1: ZONE_YELLOW, 2: ZONE_GREEN}.get(r, ZONE_YELLOW)

# Computes an event's zone using the stated emotion plus keywords in the description and context
def compute_zone(event: Dict[str, Any]) -> str:
    desc = _norm(event.get("description", ""))
    ctx = _norm(event.get("context", ""))
    amount = _norm(event.get("amount", ""))  # doesn't carry much weight yet
    emo = _norm(event.get("emotion", ""))

    # 1) Absolute priority: red keywords
    if _contains_any(desc, RED_KEYWORDS) or _contains_any(ctx, RED_KEYWORDS):
        return ZONE_RED

    # 2) Base zone from emotion
    if emo in EMOTION_TO_ZONE:
        base = EMOTION_TO_ZONE[emo]
    else:
        base = ZONE_YELLOW  # neutral if we don't know

    # 3) Soft adjustments from yellow or green keywords
    if _contains_any(desc, YELLOW_KEYWORDS) or _contains_any(ctx, YELLOW_KEYWORDS):
        base = _rank_to_zone(min(_zone_rank(base), _zone_rank(ZONE_YELLOW)))

    if _contains_any(desc, GREEN_KEYWORDS) or _contains_any(ctx, GREEN_KEYWORDS):
        base = _rank_to_zone(max(_zone_rank(base), _zone_rank(ZONE_GREEN)))

    # 4) The amount doesn't drive this yet (MVP)
    return base

# Compares the previous zone vs the current one to see if things improve, worsen, or stay the same
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

# Computes zone and trend using the last recorded event and the last zone saved in memory
def evaluate_zone_and_trend(memory: Dict[str, Any]) -> Tuple[str, str]:
    events: List[Dict[str, Any]] = memory.get("events", [])
    if not events:
        return ZONE_YELLOW, TREND_FLAT

    last_event = events[-1]
    current_zone = compute_zone(last_event)
    prev_zone = memory.get("last_zone")
    trend = compute_trend(prev_zone, current_zone)

    return current_zone, trend

# Containment mode doesn't change the zone, only the tone and the recommendation
def build_feedback(
    memory: Dict[str, Any],
    zone: str,
    trend: str,
) -> Dict[str, str]:
    containment_mode = bool(memory.get("settings", {}).get("containment_mode", False))

    # Base comment based on zone
    if zone == ZONE_GREEN:
        comment = "This shows control and clarity in the decision."
    elif zone == ZONE_YELLOW:
        comment = "There's friction; prioritize stability before optimizing."
    else:
        comment = "Critical event: focus on containment and continuity first."

    # Trend adjustment
    if trend == TREND_UP:
        comment += " The recovery is going well."
    elif trend == TREND_DOWN:
        comment += " Pressure went up; reduce friction."
    else:
        comment += " Keep the system simple."

    # Suggestion changes based on containment mode
    if containment_mode:
        if zone == ZONE_RED:
            suggestion = "Should we pause for 48h and define only what to cover first?"
        elif zone == ZONE_YELLOW:
            suggestion = "Want to activate minimum cash rules for 7 days?"
        else:
            suggestion = "Should we mark this as 'planned' so it doesn't distort the month?"
    else:
        if zone == ZONE_RED:
            suggestion = "Want us to prioritize a continuity plan (urgent things first)?"
        elif zone == ZONE_YELLOW:
            suggestion = "Want me to give you 2 quick options: soft cut vs hard cut?"
        else:
            suggestion = "Should we mark this as 'seasonal' or 'priority' for reports?"

    return {"comment": comment, "suggestion": suggestion}
