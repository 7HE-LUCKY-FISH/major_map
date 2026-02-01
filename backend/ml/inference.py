from __future__ import annotations
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
ART_DIR = REPO_ROOT / "backend" / "ml_artifacts"

def load_artifact(filename: str):
    path = ART_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing model artifact: {path}. Run training first.")
    return joblib.load(path)

def topk(pipeline, X: pd.DataFrame, k: int = 3):
    proba = pipeline.predict_proba(X)
    classes = pipeline.classes_
    idx = np.argsort(proba, axis=1)[:, -k:][:, ::-1]
    row = []
    for j in idx[0]:
        row.append({"label": str(classes[j]), "prob": float(proba[0, j])})
    return row
