# V2
from __future__ import annotations
import numpy as np


class DenseLayer:
    """
    Capa densa: toma las señales (ahorro/impulsivas/registro/fondo), las combina, y saca una salida".
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


# Semilla fija para que la demo sea estable
_rng = np.random.default_rng(7)

_dense1 = DenseLayer(n_inputs=4, n_neurons=6, rng=_rng)
_relu1 = ReLU()
_dense2 = DenseLayer(n_inputs=6, n_neurons=3, rng=_rng)


def _vectorizar_respuestas(respuestas: dict) -> np.ndarray:
    """
    Convertimos respuestas a números 0 y 1 para que sea “estable” segun orden: [ahorro, impulsivas, registra, fondo]
    """
    ahorro = float(respuestas.get("ahorro_mensual_pct", 0)) / 50.0
    impulsivas = float(respuestas.get("compras_impulsivas_sem", 0)) / 14.0
    registra = 1.0 if respuestas.get("registra_gastos", False) else 0.0
    fondo = float(respuestas.get("fondo_emergencia_meses", 0)) / 12.0

    return np.array([[ahorro, impulsivas, registra, fondo]], dtype=float)


def demo_forward_pass(respuestas: dict) -> tuple[list, float]:

# salida: 3 numeritos la “huella” que produce la red con tus respuestas
    """
    - medidor: un numero que te dice qué tan cerca estuvo de un objetivo de demo
    """
    x = _vectorizar_respuestas(respuestas)

    # Forward pass: Dense -> ReLU -> Dense
    z1 = _dense1.forward(x)
    a1 = _relu1.forward(z1)
    out = _dense2.forward(a1) 

    # Objetivo demo para explicar el concepto de mejora
    objetivo_demo = np.array([[0.6, 0.3, 0.7]], dtype=float)

    # Medidor de cercania, entre mas pequeño, mas cerca.
    medidor = float(np.mean((out - objetivo_demo) ** 2))

    return out.tolist(), medidor
    
    
    
    
# ===== DOJO V3 (PYTORCH) =====
# (loss = medida de qué tan mal predice)
# (optimizer = regla para ajustar pesos)
# (training loop = ciclo donde aprende)

import json
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from pathlib import Path
from torch.utils.data import Dataset, DataLoader

# label mapping = convertir perfil texto → id numérico
PROFILE_TO_ID = {
    "Comprador impulsivo": 0,
    "Ahorrador disciplinado": 1,
    "Genio financiero": 2,
    "Jefe de jefes": 3,
}

# ruta segura
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
HIST_PATH = _PROJECT_ROOT / "Data" / "historial.json"
MODEL_PATH = _PROJECT_ROOT / "Data" / "dojo_v3.pt"


def _vectorizar_respuestas_torch(respuestas: dict) -> list[float]:
    """
    (features = entradas numericas)
    Orden: [ahorro, impulsivas, registra, fondo]
    """
    ahorro = float(respuestas.get("ahorro_mensual_pct", 0)) / 50.0
    impulsivas = float(respuestas.get("compras_impulsivas_sem", 0)) / 14.0
    registra = 1.0 if respuestas.get("registra_gastos", False) else 0.0
    fondo = float(respuestas.get("fondo_emergencia_meses", 0)) / 12.0
    return [ahorro, impulsivas, registra, fondo]


class FinancialDataset(Dataset):
    def __init__(self, data_file: Path):
        with data_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self.X = []
        self.y = []

        for record in data:
            if record.get("type") != "run":
                continue

            respuestas = record.get("respuestas", {})
            resultado = record.get("resultado", {})
            persona = resultado.get("persona", "")

            if persona not in PROFILE_TO_ID:
                continue

            x = _vectorizar_respuestas_torch(respuestas)
            self.X.append(x)
            self.y.append(PROFILE_TO_ID[persona])

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = torch.tensor(self.X[idx], dtype=torch.float32)
        y = torch.tensor(self.y[idx], dtype=torch.long)
        return x, y


class DojoNet(nn.Module):
    def __init__(self, n_in: int = 4, n_hidden: int = 16, n_out: int = 4):
        super().__init__()
        self.fc1 = nn.Linear(n_in, n_hidden)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(n_hidden, n_out)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x


def train_on_startup(
    data_file: Path = HIST_PATH,
    epochs: int = 20,
    batch_size: int = 8,
    lr: float = 1e-3,
) -> dict:
    """
    Entrena al iniciar la app y regresa metricas básicas
    """
    if not data_file.exists():
        return {"ok": False, "reason": "no_historial", "path": str(data_file)}

    dataset = FinancialDataset(data_file)

    # Si hay muy pocos ejemplos, no entrenamos
    if len(dataset) < 8:
        return {"ok": False, "reason": "insufficient_data", "n": len(dataset)}

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = DojoNet()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    last_loss = None

    for _ in range(epochs):
        for inputs, labels in loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            last_loss = float(loss.item())

    # Guardamos pesos (state_dict = parámetros aprendidos)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)

    return {"ok": True, "n": len(dataset), "last_loss": last_loss, "model_path": str(MODEL_PATH)}

def predict_v3(respuestas: dict) -> dict:
    """
    (inference = usar el modelo ya entrenado para predecir, sin entrenar)
    Toma 'respuestas' del formulario y devuelve un dict con:
    - ok: si pudo predecir
    - pred_persona: perfil predicho
    - confidence: nivel de confianza (0 a 1)
    - probs: probabilidades por clase (lista)
    """


    # Si aun no existe el archivo entrenado, no fallamos: solo decimos "no_model"
    if not MODEL_PATH.exists():
        return {"ok": False, "reason": "no_model"}

       # Si aan no existe el archivo entrenado, no fallamos: solo decimos "no_model"
    if not MODEL_PATH.exists():
        return {"ok": False, "reason": "no_model"}

    # Convertimos respuestas a features 
    x_list = _vectorizar_respuestas_torch(respuestas)
    x = torch.tensor([x_list], dtype=torch.float32)

    # Cargamos modelo y pesos
    model = DojoNet()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()

    # Inference = usar el modelo sin entrenar
    with torch.no_grad():  
        logits = model(x) 
        probs = F.softmax(logits, dim=1).squeeze(0) 

    pred_id = int(torch.argmax(probs).item())
    conf = float(probs[pred_id].item())

    ID_TO_PROFILE = {v: k for k, v in PROFILE_TO_ID.items()}
    return {
        "ok": True,
        "pred_persona": ID_TO_PROFILE.get(pred_id, ""),
        "confidence": conf,
        "probs": [float(p.item()) for p in probs],
    }
