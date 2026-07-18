import json
from collections import Counter
from statistics import mean

# Path to the history file where everything that happened is stored
HIST = "Data/history.json"

# Confidence ranges, only to analyze how sure the model is and understand its behavior
BUCKET_EDGES = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
BUCKET_LABELS = ["0.0-0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", "0.8-0.9", "0.9-1.0"]

# High risk if it's wrong with confidence >= this
HIGH_CONF_THRESHOLD = 0.6

def bucket_of(conf: float) -> str | None:
    for i, label in enumerate(BUCKET_LABELS):
        if BUCKET_EDGES[i] <= conf < BUCKET_EDGES[i + 1]:
            return label
    return None


def main() -> None:
    with open(HIST, "r", encoding="utf-8") as f:
        events = json.load(f)

    # Keep only shadow events where V3 actually returned a valid prediction
    shadows = [
        e for e in events
        if e.get("type") == "shadow" and e.get("v3", {}).get("ok") is True
    ]

    # If there's no data, there's nothing to analyze
    if not shadows:
        print("No valid shadow events found (v3 ok=True).")
        return

    total = len(shadows)
    matches = 0

    # Collect the confidence value saved for each prediction
    confs: list[float] = []

    # Mismatch counter (V2 -> V3)
    errors = Counter()

    # Count per bucket
    bucket_total = {k: 0 for k in BUCKET_LABELS}
    bucket_ok = {k: 0 for k in BUCKET_LABELS}

    high_conf_errors: list[tuple[str, str, str, float]] = []

    for s in shadows:
        v2 = s.get("v2_profile", "")
        v3 = s.get("v3", {}).get("predicted_persona", "")
        conf = float(s.get("v3", {}).get("confidence", 0.0))
        confs.append(conf)

        b = bucket_of(conf)
        if b is not None:
            bucket_total[b] += 1

        # v3 agrees with V2
        if v2 and v3 and (v2 == v3):
            matches += 1
            if b is not None:
                bucket_ok[b] += 1
        else:

            # count mismatches
            errors[(v2, v3)] += 1

            # It was confident and still wrong: a serious error
            if v2 and v3 and conf >= HIGH_CONF_THRESHOLD and (v2 != v3):
                high_conf_errors.append((s.get("run_id", ""), v2, v3, conf))

    # Final metrics
    acc = matches / total
    avg_conf = mean(confs) if confs else 0.0

    print(f"Comparisons (valid shadows): {total}")
    print(f"Accuracy V3 vs V2: {acc:.2%}")
    print(f"Average confidence: {avg_conf:.3f}")

    print("\nAccuracy by confidence bucket:")
    for k in BUCKET_LABELS:
        if bucket_total[k] == 0:
            print(f"- {k}: (no data)")
        else:
            print(f"- {k}: {(bucket_ok[k] / bucket_total[k]):.2%}  (n={bucket_total[k]})")

    print("\nTop mismatches (V2 -> V3):")
    for (v2p, v3p), n in errors.most_common(5):
        print(f"- {v2p} -> {v3p}: {n}")

    print(f"\nHigh-confidence errors (>= {HIGH_CONF_THRESHOLD}): {len(high_conf_errors)}")
    for run_id, v2p, v3p, c in sorted(high_conf_errors, key=lambda x: -x[3])[:5]:
        print(f"- run_id={run_id} | {v2p} -> {v3p} | conf={c:.3f}")

# Entry point to run the analysis from the terminal
if __name__ == "__main__":
    main()