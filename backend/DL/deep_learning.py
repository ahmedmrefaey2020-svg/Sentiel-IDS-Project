import os
import threading
import numpy as np

from backend.dataBase.config import get_settings

_cfg = get_settings()

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "LSTM-UGRF_Final.keras")

_model = None
_load_lock = threading.Lock()


def _load_model():
    global _model
    with _load_lock:
        if _model is not None:
            return _model

        if not os.path.exists(_MODEL_PATH):
            return None

        try:
            import tensorflow as tf
            _model = tf.keras.models.load_model(_MODEL_PATH)
        except Exception:
            _model = None

        return _model


def _fallback_predict_batch(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    src_bytes = arr[:, 4]
    flow_pkts_s = arr[:, 20]
    predictions = np.where((src_bytes > 50000) | (flow_pkts_s > 100), 1, 0).astype(int)
    scores = np.where(predictions == 1, 0.9, 0.1)
    return predictions, scores


def batch_predict_dl_with_scores(arr: np.ndarray, threshold: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    model = _load_model()

    if model is None:
        return _fallback_predict_batch(arr)

    try:
        lstm_input = arr.reshape(arr.shape[0], 1, arr.shape[1])

        with _load_lock:
            probs = model.predict(lstm_input, verbose=0, batch_size=min(len(arr), 512))

        scores = probs[:, 0].astype(float)
        predictions = (scores >= threshold).astype(int)
        return predictions, scores
    except Exception:
        return _fallback_predict_batch(arr)


def batch_predict_dl(arr: np.ndarray) -> np.ndarray:
    predictions, _ = batch_predict_dl_with_scores(arr)
    return predictions


def analyze_payload_DL(payload_data: dict) -> int:
    from backend.xai import extract_features
    features = np.array([extract_features(payload_data)], dtype=np.float32)
    results = batch_predict_dl(features)
    return int(results[0])
