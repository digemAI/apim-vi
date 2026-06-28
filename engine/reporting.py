from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Import core rule logic
from engine.rules import (
    compute_zone,
    compute_trend,
    build_feedback,
    ZONE_GREEN,
    ZONE_YELLOW,
    ZONE_RED,
)

# Helper functions
def _norm(s: str) -> str:

    # Cleans text
    return (s or "").strip()

# Gets a value from the dict and normalizes it
def _safe_get(d: Dict[str, Any], key: str, default: str = "") -> str:
    v = d.get(key, default)
    return _norm(str(v))

# Event selection
def _last_n_events(memory: Dict[str, Any], n: int = 5) -> List[Dict[str, Any]]:

    # Takes the last N events from memory
    events = memory.get("events", [])
    if not events:
        return []
    return events[-n:]

# Converts raw events into reportable rows:
def _make_rows(events: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Date | Event | Amount | Context | Emotion | Zone | Trend
    """
    rows: List[Dict[str, str]] = []
    prev_zone = None

    for e in events:

        # Zone per event
        z = compute_zone(e)

        # Trend within the report (compared to the previous event)
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

# Counts how many events fell into each zone
def _zone_counts(rows: List[Dict[str, str]]) -> Tuple[int, int, int]:
    g = sum(1 for r in rows if r["zone"] == ZONE_GREEN)
    y = sum(1 for r in rows if r["zone"] == ZONE_YELLOW)
    r = sum(1 for r in rows if r["zone"] == ZONE_RED)
    return g, y, r

# Weekly overall zone
def _overall_zone(rows: List[Dict[str, str]]) -> str:
    """
    MVP rule for the weekly overall zone:
    - >= 2 reds -> red
    - 1 red -> yellow (there was a critical event)
    - >= 2 yellows -> yellow
    - otherwise -> green
    """
    g, y, r = _zone_counts(rows)

    if r >= 2:
        return ZONE_RED
    if r == 1:
        return ZONE_YELLOW
    if y >= 2:
        return ZONE_YELLOW
    return ZONE_GREEN


# Compares the current overall zone against the last weekly snapshot if it exists, otherwise against memory["last_zone"]
def _overall_trend(memory: Dict[str, Any], overall_zone: str) -> str:
    prev_zone = None

    snaps = memory.get("weekly_snapshots", [])
    if snaps:
        prev_zone = snaps[-1].get("overall_zone")

    if not prev_zone:
        prev_zone = memory.get("last_zone")

    return compute_trend(prev_zone, overall_zone)

# Table printing
def _print_table(rows: List[Dict[str, str]]) -> None:

    # Headers and fixed widths
    headers = ["Date", "Event", "Amount", "Context", "Emotion", "Zone", "Trend"]
    col_widths = [10, 24, 10, 18, 12, 4, 5]

    # Truncates long text so it doesn't break the table
    def cut(text: str, width: int) -> str:
        t = (text or "")
        if len(t) <= width:
            return t.ljust(width)
        return (t[: width - 1] + "…").ljust(width)

    # Header line
    line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    sep = "-+-".join("-" * w for w in col_widths)

    print("\n" + line)
    print(sep)

    # Rows
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


# Uses the last N events, prints table + summary, and saves a snapshot if requested to build the weekly report
def weekly_report(
    memory: Dict[str, Any],
    n_events: int = 5,
    save_snapshot: bool = True
) -> Dict[str, Any]:

    events = _last_n_events(memory, n=n_events)
    if not events:
        print("\n📊 APIM VI — Weekly Report")
        print("No events recorded yet.")
        return {"ok": False, "reason": "no_events"}

    # Build rows and print the table
    rows = _make_rows(events)
    _print_table(rows)

    # Overall zone and trend
    overall_zone = _overall_zone(rows)
    overall_trend = _overall_trend(memory, overall_zone)

    # comment + suggestion based on zone and trend
    fb = build_feedback(memory, overall_zone, overall_trend)
    g, y, r = _zone_counts(rows)

    # Final summary
    print("\n📌 Weekly Summary")
    print(f"- Events analyzed: {len(rows)}")
    print(f"- Zone count: 🟢{g}  🟡{y}  🔴{r}")
    print(f"- Overall zone: {overall_zone}")
    print(f"- Trend: {overall_trend}")
    print(f"- Insight: {fb['comment']}")
    print(f"- Suggestion: {fb['suggestion']}")

    # Snapshot saved to memory
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
