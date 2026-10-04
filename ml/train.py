"""
ml/train.py
RandomForestClassifier with Isotonic Calibration for Re:Learn.
STATUS: PAUSED — DO NOT RUN until Phase 5 is approved.
"""
import os
import json

MODEL_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "model.joblib")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "metrics.json")
DATASET_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "dataset.json")


def train():
    """Train a calibrated RandomForest on the generated dataset."""
    import json
    import joblib
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import LabelEncoder
    from backend.app.core.features import extract_ast_features, generate_execution_signature

    print("📖 Loading dataset...")
    with open(DATASET_PATH) as f:
        data = json.load(f)

    X, y = [], []
    for sample in data:
        feats = extract_ast_features(sample["code"])
        sig = generate_execution_signature(sample["code"])
        # Flatten features into numeric vector
        feat_vec = [
            int(feats.get("accumulator_inside_loop", False)),
            int(feats.get("has_return", False)),
            int(feats.get("has_print_call", False)),
            int(feats.get("uses_range_len_minus_one", False)),
            int(feats.get("has_comparison_lt_update", False)),
            int(feats.get("calls_list_reverse", False)),
            int(feats.get("builds_new_list", False)),
            int(feats.get("reverse_range_excludes_zero", False)),
            int(feats.get("has_indentation_issue", False)),
            int(feats.get("indentation_after_colon_missing", False)),
            int(feats.get("parse_error", False)),
            feats.get("loop_count", 0),
        ]
        X.append(feat_vec)
        y.append(sample["label"])

    X = np.array(X)
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    base = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    clf = CalibratedClassifierCV(base, method="isotonic", cv=5)
    clf.fit(X, y_enc)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": clf, "label_encoder": le}, MODEL_PATH)

    # Evaluate
    scores = cross_val_score(clf, X, y_enc, cv=5, scoring="f1_macro")
    metrics = {
        "macro_f1": round(float(scores.mean()), 4),
        "std": round(float(scores.std()), 4),
        "classes": list(le.classes_),
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Model trained. Macro F1: {metrics['macro_f1']:.4f}")


if __name__ == "__main__":
    print("[+] Phase 5 Resumed: Training Random Forest Classifier...")
    train()
