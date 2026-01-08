import json
from collections import Counter
from statistics import mean

# Ruta al historial donde quedo todo lo que ha pasado
HIST = "Data/historial.json"

# Rangos de confidence solo para analizar que tan seguro anda el modelo y entender su comportamiento
BUCKET_EDGES = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
BUCKET_LABELS = ["0.0-0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", "0.8-0.9", "0.9-1.0"]

# alto riesgo si se equivoca con >= esto
HIGH_CONF_THRESHOLD = 0.6  

def bucket_of(conf: float) -> str | None:
    for i, label in enumerate(BUCKET_LABELS):
        if BUCKET_EDGES[i] <= conf < BUCKET_EDGES[i + 1]:
            return label
    return None


def main() -> None:
    with open(HIST, "r", encoding="utf-8") as f:
        events = json.load(f)

# Nos quedamos solo con eventos shadow donde V3 sí dio predicción válida
    shadows = [
        e for e in events
        if e.get("type") == "shadow" and e.get("v3", {}).get("ok") is True
    ]

# Si no hay datos, no hay nada que analizar
    if not shadows:
        print("No hay eventos shadow válidos (v3 ok=True).")
        return

    total = len(shadows)
    matches = 0

# Sacamos el promedio que se guardo  de todas las confidence 
    confs: list[float] = []

# Contador de errores (V2 -> V3)
    errors = Counter() # 

# Conteo por rango
    bucket_total = {k: 0 for k in BUCKET_LABELS}
    bucket_ok = {k: 0 for k in BUCKET_LABELS}

    high_conf_errors: list[tuple[str, str, str, float]] = []

    for s in shadows:
        v2 = s.get("v2_persona", "") 
        v3 = s.get("v3", {}).get("pred_persona", "")
        conf = float(s.get("v3", {}).get("confidence", 0.0))
        confs.append(conf)

        b = bucket_of(conf)
        if b is not None:
            bucket_total[b] += 1

        # v3 coincide con V2
        if v2 and v3 and (v2 == v3):
            matches += 1
            if b is not None:
                bucket_ok[b] += 1
        else:

            # contamos confusiones
            errors[(v2, v3)] += 1

             # Estaba seguro y aún así se equivoco, error serio
            if v2 and v3 and conf >= HIGH_CONF_THRESHOLD and (v2 != v3):
                high_conf_errors.append((s.get("run_id", ""), v2, v3, conf))

 # Metricas finales
    acc = matches / total
    avg_conf = mean(confs) if confs else 0.0

    print(f"Comparaciones (shadow válidos): {total}")
    print(f"Accuracy V3 vs V2: {acc:.2%}")
    print(f"Confidence promedio: {avg_conf:.3f}")

    print("\nAccuracy por bucket de confidence:")
    for k in BUCKET_LABELS:
        if bucket_total[k] == 0:
            print(f"- {k}: (sin datos)")
        else:
            print(f"- {k}: {(bucket_ok[k] / bucket_total[k]):.2%}  (n={bucket_total[k]})")

    print("\nTop errores (V2 -> V3):")
    for (v2p, v3p), n in errors.most_common(5):
        print(f"- {v2p} -> {v3p}: {n}")

    print(f"\nErrores con alta confidence (>= {HIGH_CONF_THRESHOLD}): {len(high_conf_errors)}")
    for run_id, v2p, v3p, c in sorted(high_conf_errors, key=lambda x: -x[3])[:5]:
        print(f"- run_id={run_id} | {v2p} -> {v3p} | conf={c:.3f}")

# Punto de entrada para correr el análisis desde terminal
if __name__ == "__main__":
    main()

