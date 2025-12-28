# Importamos las funciones y constantes que queremos probar
from apim_vi.rules import (
    compute_zone,       # decide 🟢🟡🔴 por evento
    compute_trend,      # decide 📈➖📉 por cambio de zona
    build_feedback,     # genera comentarios y sugerencias
    ZONE_GREEN,
    ZONE_YELLOW,
    ZONE_RED,
    TREND_UP,
    TREND_DOWN,
    TREND_FLAT,
)


def test_compute_zone_green_by_emotion():
    # Simula un evento tranquilo y planeado
    event = {
        "description": "Viaje familiar",
        "context": "diversión",
        "emotion": "tranquilo"
    }

    # Esperamos que caiga en zona verde
    assert compute_zone(event) == ZONE_GREEN


def test_compute_zone_yellow_by_emotion():
    event = {
        "description": "Cambio laboral",
        "context": "necesito empleo",
        "emotion": "estrés"
    }

    # El estrés debe llevar a zona amarilla
    assert compute_zone(event) == ZONE_YELLOW


def test_compute_zone_red_by_keyword():
    event = {
        "description": "Me robaron el carro",
        "context": "estaba durmiendo",
        "emotion": "enojo"
    }

    # Palabra clave "robaron" fuerza zona roja
    assert compute_zone(event) == ZONE_RED


def test_compute_trend_up_down_flat():
    # Mejora → tendencia positiva
    assert compute_trend(ZONE_YELLOW, ZONE_GREEN) == TREND_UP

    # Empeora → tendencia negativa
    assert compute_trend(ZONE_GREEN, ZONE_YELLOW) == TREND_DOWN

    # Igual → estable
    assert compute_trend(ZONE_RED, ZONE_RED) == TREND_FLAT

    # Sin histórico → neutro
    assert compute_trend(None, ZONE_YELLOW) == TREND_FLAT


def test_compute_trend_up_down_flat():
    # Mejora → tendencia positiva
    assert compute_trend(ZONE_YELLOW, ZONE_GREEN) == TREND_UP

    # Empeora → tendencia negativa
    assert compute_trend(ZONE_GREEN, ZONE_YELLOW) == TREND_DOWN

    # Igual → estable
    assert compute_trend(ZONE_RED, ZONE_RED) == TREND_FLAT

    # Sin histórico → neutro
    assert compute_trend(None, ZONE_YELLOW) == TREND_FLAT
