# “Dojo” = red neuronal sencilla en NumPy.
# No entrena todavía (no hay backward/optimizer), pero sí:
# - tiene pesos + sesgos
# - procesa tus respuestas (forward pass)
# - Daa una salida numérica + un “medidor” de cercanía (concepto de mejora futura)
from __future__ import annotations

import numpy as np


class DenseLayer:
    """
    Capa densa: conecta todo con todo.
    Piensa en esto como:
    "tomo tus señales (ahorro/impulsivas/registro/fondo), las combino, y saco una salida".
    """
    def __init__(self, n_inputs: int, n_neurons: int, rng: np.random.Generator):
        # Pesos pequeños al inicio para que no se vuelva loco con números gigantes
        self.weights = 0.01 * rng.standard_normal((n_inputs, n_neurons))
        # Sesgos: el “empujoncito” que permite activar neuronas aunque la señal sea baja
        self.biases = np.zeros((1, n_neurons), dtype=float)

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        return inputs @ self.weights + self.biases


class ReLU:
    """
    ReLU: filtro simple.
    Si algo sale negativo, lo corta a 0. Si es positivo, lo deja pasar.
    """
    def forward(self, inputs: np.ndarray) -> np.ndarray:
        return np.maximum(0, inputs)


# Semilla fija para que la demo sea estable (no cambie cada vez que corres Streamlit)
_rng = np.random.default_rng(7)

_dense1 = DenseLayer(n_inputs=4, n_neurons=6, rng=_rng)
_relu1 = ReLU()
_dense2 = DenseLayer(n_inputs=6, n_neurons=3, rng=_rng)


def _vectorizar_respuestas(respuestas: dict) -> np.ndarray:
    """
    Convertimos tus respuestas a números 0..1 (para que sea “estable”).
    Orden: [ahorro, impulsivas, registra, fondo]
    """
    ahorro = float(respuestas.get("ahorro_mensual_pct", 0)) / 50.0
    impulsivas = float(respuestas.get("compras_impulsivas_sem", 0)) / 14.0
    registra = 1.0 if respuestas.get("registra_gastos", False) else 0.0
    fondo = float(respuestas.get("fondo_emergencia_meses", 0)) / 12.0

    return np.array([[ahorro, impulsivas, registra, fondo]], dtype=float)


def demo_forward_pass(respuestas: dict) -> tuple[list, float]:
    """
    Regresa:
    - salida: 3 numeritos (la “huella” que produce la red con tus respuestas)
    - medidor: un número que te dice qué tan cerca estuvo de un objetivo de demo
    """
    x = _vectorizar_respuestas(respuestas)

    # Forward pass: Dense -> ReLU -> Dense
    z1 = _dense1.forward(x)
    a1 = _relu1.forward(z1)
    out = _dense2.forward(a1)  # shape (1,3)

    # “Objetivo demo” (solo para explicar el concepto de mejora)
    objetivo_demo = np.array([[0.6, 0.3, 0.7]], dtype=float)

    # “Medidor” de cercanía (sin decir MSE ni clavarnos en matemáticas)
    # Entre más pequeño, más cerca.
    medidor = float(np.mean((out - objetivo_demo) ** 2))

    return out.tolist(), medidor
