import threading
import time
from collections import deque
from datetime import datetime

from scapy.all import sniff, IP, TCP, UDP

from backend.dataBase.config import get_settings
from backend.dataBase.database import get_cached_monitoring_config, SessionLocal
from backend.dataBase.models import NetworkFlow, SystemSetting
from backend.services.ip_service import sync_block_ip, is_ip_blocked_sync
from backend.handlers.packets_handler import _extract_packet_features, _packet_callback, _clear_packet_queue
from backend.handlers.stats_handler import update_last_external_time

_cfg = get_settings()
_packet_queue: deque = deque(maxlen=_cfg.BATCH_SIZE * 2)
_queue_lock = threading.Lock()
_db_write_queue: deque = deque(maxlen=20000)
_db_write_lock = threading.Lock()
db = SessionLocal()
lastest_model = db.query(SystemSetting.active_model).first() if db.query(SystemSetting.active_model).first() else "lstm",
_stats = {
    "connections": 0,
    "packet_rate": 0,
    "score": 5,
    "message": "System is stable.",
    "is_anomaly": False,
    "recent_flows": deque(maxlen=_cfg.MAX_RECENT_FLOWS),
    "model": lastest_model,
    "inbound_bytes": 0,
    "outbound_bytes": 0,
    "dropped_packets": 0,
    "active_iocs": 0,
    "malicious_blocked": 0,
    "targeted_attacks": 0,
}
_stats_lock = threading.Lock()

_stop_event = threading.Event()
_threads: list[threading.Thread] = []


def _run_predictions(arr, model_type: str, confidence: int):
    import numpy as np

    try:
        if model_type == "lstm":
            from backend.DL.deep_learning import batch_predict_dl_with_scores
            return batch_predict_dl_with_scores(arr, confidence / 100.0)
        from backend.ML.machine_learning import batch_predict_ml_with_scores
        return batch_predict_ml_with_scores(arr, confidence / 100.0)
    except Exception:
        return np.zeros(len(arr), dtype=int), np.zeros(len(arr), dtype=float)


def _apply_batch_results(
    metadata: list[tuple],
    predictions,
    scores,
    auto_block: bool,
):
    now_str = datetime.now().strftime("%H:%M:%S")
    anomaly_count = 0
    new_flows = []

    for i, (src_ip, dst_ip, port, src_bytes, protocol) in enumerate(metadata):
        pred = int(predictions[i]) if i < len(predictions) else 0
        if pred == 1:
            anomaly_count += 1
            if auto_block and not is_ip_blocked_sync(src_ip):
                sync_block_ip(src_ip, protocol, int(port), float(src_bytes))

        new_flows.append({
            "time": now_str,
            "src": src_ip,
            "dest": dst_ip,
            "port": int(port),
            "proto": protocol,
            "status": "anomaly" if pred == 1 else "normal",
            "score": float(scores[i]) if i < len(scores) else 0.0,
            "confidence": float(scores[i]) * 100 if i < len(scores) else 0.0, 
        })

        if pred == 1 or (i % 50 == 0):
            with _db_write_lock:
                _db_write_queue.append({
                    "time": now_str,
                    "src": src_ip,
                    "dest": dst_ip,
                    "proto": str(protocol).upper(),
                    "packets": 1,
                    "is_attack": pred == 1,
                    "label": "Anomaly" if pred == 1 else "Normal",
                })

    batch_len = max(len(metadata), 1)
    is_anomaly = anomaly_count > 0
    score = min(99, int((anomaly_count / batch_len) * 100) + 5) if is_anomaly else 5
    msg = (
        f"Batch: {anomaly_count}/{batch_len} anomalies detected."
        if is_anomaly
        else f"Batch clean: {batch_len} connections analyzed."
    )

    with _stats_lock:
        _stats["connections"] += len(metadata)
        _stats["packet_rate"] = len(metadata)
        _stats["is_anomaly"] = is_anomaly
        _stats["score"] = score
        _stats["message"] = msg
        for flow in new_flows[-_cfg.MAX_RECENT_FLOWS:]:
            _stats["recent_flows"].append(flow)


def _process_batch(packets: list, model_type: str, confidence: int, auto_block: bool):
    if not packets:
        return

    from backend.xai import extract_features
    import numpy as np

    features_matrix = []
    metadata = []

    for pkt in packets:
        try:
            payload, src_ip, dst_ip, port, src_bytes, protocol = _extract_packet_features(pkt)
            features_matrix.append(extract_features(payload))
            metadata.append((src_ip, dst_ip, port, src_bytes, protocol))
        except Exception:
            continue

    if not features_matrix:
        return

    arr = np.array(features_matrix, dtype=np.float32)
    predictions, scores = _run_predictions(arr, model_type, confidence)
    _apply_batch_results(metadata, predictions, scores, auto_block)


def _batch_processor_loop():
    while not _stop_event.is_set():
        try:
            mode, model_type, confidence, auto_block = get_cached_monitoring_config()

            if mode == "api_agent":
                _clear_packet_queue()
                time.sleep(0.5)
                continue

            batch = []
            with _queue_lock:
                while _packet_queue and len(batch) < _cfg.BATCH_SIZE:
                    batch.append(_packet_queue.popleft())

            if batch:
                _process_batch(batch, model_type, confidence, auto_block)
            else:
                time.sleep(0.05)
        except Exception:
            time.sleep(0.1)


def _db_writer_loop():
    while not _stop_event.is_set():
        try:
            time.sleep(_cfg.DB_WRITER_INTERVAL)
            records = []
            with _db_write_lock:
                while _db_write_queue:
                    records.append(_db_write_queue.popleft())

            if not records:
                continue

            db = SessionLocal()
            try:
                objs = [
                    NetworkFlow(
                        time=r["time"],
                        src=r["src"],
                        dest=r["dest"],
                        proto=r["proto"],
                        duration="0.0",
                        packets=r["packets"],
                        is_attack=r["is_attack"],
                        label=r["label"],
                    )
                    for r in records
                ]
                db.bulk_save_objects(objs)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
        except Exception:
            time.sleep(1.0)


def _sniff_loop():
    while not _stop_event.is_set():
        try:
            mode, _, _, _ = get_cached_monitoring_config()
            if mode != "scapy":
                _clear_packet_queue()
                time.sleep(1.0)
                continue
            sniff(
                prn=_packet_callback,
                store=False,
                timeout=_cfg.SNIFF_TIMEOUT,
            )
        except Exception:
            time.sleep(1.0)

def start_monitor():
    global _threads
    if _threads and any(t.is_alive() for t in _threads):
        return

    _stop_event.clear()
    _threads = [
        threading.Thread(target=_sniff_loop, daemon=True, name="sentinel-sniff"),
        threading.Thread(target=_batch_processor_loop, daemon=True, name="sentinel-batch"),
        threading.Thread(target=_db_writer_loop, daemon=True, name="sentinel-db"),
    ]
    for t in _threads:
        t.start()


def stop_monitor():
    _stop_event.set()
    for t in _threads:
        t.join(timeout=2.0)


def ingest_external_batch(
    records_features: list[list[float]],
    metadata: list[dict],
    model_type: str,
) -> dict:
    import numpy as np

    update_last_external_time()

    _, _, confidence, auto_block = get_cached_monitoring_config()
    arr = np.array(records_features, dtype=np.float32)
    predictions, scores = _run_predictions(arr, model_type, confidence)

    meta_tuples = []
    for i, feat in enumerate(records_features):
        meta = metadata[i] if i < len(metadata) else {}
        meta_tuples.append((
            meta.get("src", "0.0.0.0"),
            meta.get("dest", "0.0.0.0"),
            int(meta.get("port", 0)),
            float(meta.get("src_bytes", feat[4] if len(feat) > 4 else 0.0)),
            meta.get("proto", "TCP"),
        ))

    _apply_batch_results(meta_tuples, predictions, scores, auto_block)

    total = len(predictions)
    attacks = int(sum(1 for p in predictions if int(p) == 1))
    return {
        "total": total,
        "attacks": attacks,
        "normals": total - attacks,
        "predictions": [int(p) for p in predictions],
    }
