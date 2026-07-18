# V2
from __future__ import annotations
import numpy as np


class DenseLayer:
    """
    Fully connected layer: combine input signals through weights and biases
    to produce a transformed output.
    """
    def __init__(self, n_inputs: int, n_neurons: int, rng: np.random.Generator):

        # Small initial weights prevent exploding activations early in training.
        self.weights = 0.01 * rng.standard_normal((n_inputs, n_neurons))

        # Biases let neurons activate even when the input signal is weak.
        self.biases = np.zeros((1, n_neurons), dtype=float)

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        return inputs @ self.weights + self.biases


class ReLU:
    """
    pass positive values unchanged, clip negatives to zero.
    """
    def forward(self, inputs: np.ndarray) -> np.ndarray:
        return np.maximum(0, inputs)


# Fixing the seed guarantees reproducible results for the demo.
_rng = np.random.default_rng(7)

_dense1 = DenseLayer(n_inputs=4, n_neurons=6, rng=_rng)
_relu1 = ReLU()
_dense2 = DenseLayer(n_inputs=6, n_neurons=3, rng=_rng)


def _vectorize_answers(answers: dict) -> np.ndarray:
    """
    Normalize survey answers to [0, 1] for stable network input.
    Order: [savings, impulsive, tracks, fund]
    """
    savings = float(answers.get("monthly_savings_pct", 0)) / 50.0
    impulsive = float(answers.get("impulsive_purchases_week", 0)) / 14.0
    tracks = 1.0 if answers.get("tracks_expenses", False) else 0.0
    fund = float(answers.get("emergency_fund_months", 0)) / 12.0

    return np.array([[savings, impulsive, tracks, fund]], dtype=float)


def demo_forward_pass(answers: dict) -> tuple[list, float]:
    """
    Executes a single forward pass for demonstration.

    Returns:
        - output: 3-value activation vector (the network's fingerprint for these answers).
        - distance_score: mean squared distance to a fixed demo target; (lower is better).
    """
    x = _vectorize_answers(answers)

    # Standard forward pass: Dense -> ReLU -> Dense
    raw_output = _dense1.forward(x)
    activated_output = _relu1.forward(raw_output)
    out = _dense2.forward(activated_output)

    # A fixed target used only to illustrate model improvement.
    demo_target = np.array([[0.6, 0.3, 0.7]], dtype=float)

    # Proximity score: a lower score means it's closer to the target.
    distance_score = float(np.mean((out - demo_target) ** 2))

    return out.tolist(), distance_score


# ===== DOJO V3 (PYTORCH) =====
# loss     — Measures the discrepancy between predictions and actual targets.
# optimizer — The algorithm that updates the model's weights to minimize the loss.
# training loop — the cycle where the model learns from data

import json
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from pathlib import Path
from torch.utils.data import Dataset, DataLoader

# Encodes profile categories into class indices.
# Must match the persona names returned by engine.core.classify() exactly.
PROFILE_TO_ID = {
    "Impulse Buyer": 0,
    "Disciplined Saver": 1,
    "Financial Strategist": 2,
    "Money Boss": 3,
}

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
HIST_PATH = _PROJECT_ROOT / "Data" / "history.json"
MODEL_PATH = _PROJECT_ROOT / "Data" / "dojo_v3.pt"


def _vectorize_answers_torch(answers: dict) -> list[float]:
    """
    Compress survey answers to [0, 1] so all features enter the network
    at comparable magnitudes.

    Order: [savings, impulsive, tracks, fund]
    """
    savings = float(answers.get("monthly_savings_pct", 0)) / 50.0
    impulsive = float(answers.get("impulsive_purchases_week", 0)) / 14.0
    tracks = 1.0 if answers.get("tracks_expenses", False) else 0.0
    fund = float(answers.get("emergency_fund_months", 0)) / 12.0
    return [savings, impulsive, tracks, fund]


class FinancialDataset(Dataset):
    """
    Prepares financial survey records for PyTorch consumption
    """
    def __init__(self, data_file: Path):
        with data_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self.X = []
        self.y = []

        for record in data:
            if record.get("type") != "run":
                continue

            answers = record.get("answers", {})
            result = record.get("result", {})
            profile_label = result.get("profile", "")

            if profile_label not in PROFILE_TO_ID:
                continue

            x = _vectorize_answers_torch(answers)
            self.X.append(x)
            self.y.append(PROFILE_TO_ID[profile_label])

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        features = torch.tensor(self.X[idx], dtype=torch.float32)
        label = torch.tensor(self.y[idx], dtype=torch.long)
        return features, label


class DojoNet(nn.Module):
    """
    Neural network architecture for financial profile classification.
    """

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
    Trains the model on application startup and returns training metrics.
    Skips training if the history file is missing or contains insufficient records.
    """
    if not data_file.exists():
        return {"ok": False, "reason": "no_history_file", "path": str(data_file)}

    dataset = FinancialDataset(data_file)

    # Aborts training if the dataset is too small to generalize.
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

    # Persist the learned weights so predict_v3 can load them without retraining.
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)

    return {"ok": True, "n": len(dataset), "last_loss": last_loss, "model_path": str(MODEL_PATH)}


def predict_v3(answers: dict) -> dict:
    """
    Evaluates survey answers against the trained model to classify the user.

    Returns:
        - ok: True if the model loaded and ran successfully.
        - predicted_persona: The resulting financial profile.
        - confidence: Probability of the predicted profile [0, 1].
        - probs: The probability distribution for all possible classes.
    """

    # Aborts inference if the saved weights are missing
    if not MODEL_PATH.exists():
        return {"ok": False, "reason": "no_model"}

    input_vector = _vectorize_answers_torch(answers)
    input_tensor = torch.tensor([input_vector], dtype=torch.float32)

    # Initializes the network architecture and loads the saved weights.
    model = DojoNet()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()

    # Disables gradient computation to optimize inference performance.
    with torch.no_grad():
        logits = model(input_tensor)
        probs = F.softmax(logits, dim=1).squeeze(0)

    pred_id = int(torch.argmax(probs).item())
    conf = float(probs[pred_id].item())

    ID_TO_PROFILE = {v: k for k, v in PROFILE_TO_ID.items()}
    return {
        "ok": True,
        "predicted_persona": ID_TO_PROFILE.get(pred_id, ""),
        "confidence": conf,
        "probs": [float(p.item()) for p in probs],
    }