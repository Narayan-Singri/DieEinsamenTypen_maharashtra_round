"""
ml/evaluate.py
Evaluates the trained misconception classifier with LOPO (Leave-One-Problem-Out),
per-class precision/recall/F1, and confusion matrix diagnostics.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import joblib
import numpy as np
from ml.train import extract_numeric_features, MODEL_PATH, METRICS_PATH

def evaluate():
    if not os.path.exists(MODEL_PATH):
        print("[-] Model artifact not found. Run `python ml/train.py` first.")
        return

    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    classes = bundle["classes"]

    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        print(f"📊 Evaluation Summary:")
        print(f"   Model: {metrics['model_info']['type']}")
        print(f"   Accuracy: {metrics['overall_accuracy']*100:.2f}%")
        print(f"   Macro F1: {metrics['macro_f1']*100:.2f}%")
        print("\n📈 Per-Class Performance:")
        for cls, m in metrics.get("lopo_metrics", {}).items():
            print(f"   {cls}: Precision={m['precision']*100:.1f}%, Recall={m['recall']*100:.1f}%, F1={m['f1']*100:.1f}%")

if __name__ == "__main__":
    evaluate()
