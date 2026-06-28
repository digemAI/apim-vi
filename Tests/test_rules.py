# Import the functions and constants we want to test
from engine.rules import (
    compute_zone,       # decides 🟢🟡🔴 per event
    compute_trend,      # decides 📈➖📉 from a zone change
    build_feedback,     # generates comments and suggestions
    ZONE_GREEN,
    ZONE_YELLOW,
    ZONE_RED,
    TREND_UP,
    TREND_DOWN,
    TREND_FLAT,
)


def test_compute_zone_green_by_emotion():
    # Simulates a calm, planned event
    event = {
        "description": "Family trip",
        "context": "fun",
        "emotion": "calm"
    }

    # We expect it to land in the green zone
    assert compute_zone(event) == ZONE_GREEN


def test_compute_zone_yellow_by_emotion():
    event = {
        "description": "Job change",
        "context": "need a job",
        "emotion": "stress"
    }

    # Stress should lead to the yellow zone
    assert compute_zone(event) == ZONE_YELLOW


def test_compute_zone_red_by_keyword():
    event = {
        "description": "My car got stolen last night",
        "context": "I was asleep",
        "emotion": "anger"
    }

    # Keyword "stolen" forces the red zone
    assert compute_zone(event) == ZONE_RED


def test_compute_trend_up_down_flat():
    # Improves -> positive trend
    assert compute_trend(ZONE_YELLOW, ZONE_GREEN) == TREND_UP

    # Worsens -> negative trend
    assert compute_trend(ZONE_GREEN, ZONE_YELLOW) == TREND_DOWN

    # Same -> flat
    assert compute_trend(ZONE_RED, ZONE_RED) == TREND_FLAT

    # No history -> neutral
    assert compute_trend(None, ZONE_YELLOW) == TREND_FLAT
