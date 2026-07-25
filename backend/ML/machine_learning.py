import os
import threading
import numpy as np
import joblib

from backend.dataBase.config import get_settings

_cfg = get_settings()

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "RandomForest_Model.pkl")
_SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler_rf.pkl")

_model = None
_scaler = None
_load_lock = threading.Lock()


def _load_model():
    global _model, _scaler
    with _load_lock:
        if _model is not None:
            return _model

        if not os.path.exists(_MODEL_PATH):
            return None

        try:
            _model = joblib.load(_MODEL_PATH)
            if os.path.exists(_SCALER_PATH):
                _scaler = joblib.load(_SCALER_PATH)
        except Exception:
            _model = None

        return _model


def _fallback_predict_batch(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    src_bytes = arr[:, 4]
    flow_pkts_s = arr[:, 20]
    predictions = np.where((src_bytes > 50000) | (flow_pkts_s > 100), 1, 0).astype(int)
    scores = np.where(predictions == 1, 0.9, 0.1)
    return predictions, scores


def batch_predict_ml_with_scores(arr: np.ndarray, threshold: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    model = _load_model()

    if model is None:
        return _fallback_predict_batch(arr)

    try:
        features = arr
        if _scaler is not None:
            features = _scaler.transform(arr)

        with _load_lock:
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(features)
                if proba.ndim == 2 and proba.shape[1] >= 2:
                    scores = proba[:, 1]
                else:
                    scores = proba.ravel()
                predictions = (scores >= threshold).astype(int)
            else:
                predictions = model.predict(features).astype(int)
                scores = predictions.astype(float)

        return predictions, scores.astype(float)
    except Exception:
        return _fallback_predict_batch(arr)


def batch_predict_ml(arr: np.ndarray) -> np.ndarray:
    predictions, _ = batch_predict_ml_with_scores(arr)
    return predictions


def analyze_payload_ML(payload_data: dict) -> int:
    from backend.xai import extract_features
    features = np.array([extract_features(payload_data)], dtype=np.float32)
    results = batch_predict_ml(features)
    return int(results[0])
