import threading
import time
from collections import deque
from datetime import datetime

from scapy.all import sniff, IP, TCP, UDP

from backend.dataBase.config import get_settings
from backend.dataBase.database import SessionLocal
from backend.dataBase.models import SystemSetting


_cfg = get_settings()

db = SessionLocal()
try:
    db_model = db.query(SystemSetting.active_model).first()
    latest_model = db_model[0] if db_model and db_model[0] else "lstm"
except Exception:
    latest_model = "lstm"
finally:
    db.close()

_stats = {
    "connections": 0,
    "packet_rate": 0,
    "score": 5.0,
    "message": "System is stable.",
    "is_anomaly": False,
    "recent_flows": deque(maxlen=_cfg.MAX_RECENT_FLOWS),
    "model": latest_model,
    "inbound_bytes": 0,
    "outbound_bytes": 0,
    "dropped_packets": 0,
    "active_iocs": 0,
    "malicious_blocked": 0,
    "targeted_attacks": 0,
    "syn_rate": 0.0,
    "ack_rate": 0.0,
    "syn_packet_count": 0,
    "ack_packet_count": 0,
}

_stats_lock = threading.Lock()

_last_external_data_time: float = 0.0
_external_time_lock = threading.Lock()


def get_stats() -> dict:
    with _stats_lock:
        recent_flows_list = list(_stats["recent_flows"])
        
        inb_bytes = _stats.get("inbound_bytes", sum(f.get("byte_count", 0) for f in recent_flows_list if f.get("direction") == "inbound"))
        out_bytes = _stats.get("outbound_bytes", sum(f.get("byte_count", 0) for f in recent_flows_list if f.get("direction") == "outbound"))
        
        drop_pkts = _stats.get("dropped_packets", sum(f.get("dropped_packets", 0) or f.get("packet_drops", 0) for f in recent_flows_list))
        
        iocs = _stats.get("active_iocs", len([f for f in recent_flows_list if f.get("is_ioc") or f.get("has_ioc")]))
        
        blocked = _stats.get("malicious_blocked", len([f for f in recent_flows_list if f.get("status") == "blocked" or f.get("blocked")]))
        
        targeted = _stats.get("targeted_attacks", len([f for f in recent_flows_list if f.get("attack_type") or f.get("is_targeted")]))

        return {
            "connections": _stats["connections"],
            "packet_rate": _stats["packet_rate"],
            "score": _stats["score"],
            "model": _stats["model"],
            "message": _stats["message"],
            "is_anomaly": _stats["is_anomaly"],
            "recent_flows": recent_flows_list,
            "inbound_bytes": inb_bytes,
            "outbound_bytes": out_bytes,
            "dropped_packets": drop_pkts,
            "active_iocs": iocs,
            "malicious_blocked": blocked,
            "targeted_attacks": targeted,
            "syn_rate": _stats.get("syn_rate", 0.0),
            "ack_rate": _stats.get("ack_rate", 0.0),
            "syn_packet_count": _stats.get("syn_packet_count", 0),
            "ack_packet_count": _stats.get("ack_packet_count", 0),
        }


def update_stats(new_data: dict):
    global _stats
    with _stats_lock:
        for key, value in new_data.items():
            if key in _stats:
                _stats[key] = value


def update_last_external_time():
    global _last_external_data_time
    with _external_time_lock:
        _last_external_data_time = time.time()


def get_last_external_time() -> float:
    with _external_time_lock:
        return _last_external_data_time


def is_agent_offline() -> bool:
    last = get_last_external_time()
    if last <= 0:
        return True
    return (time.time() - last) > _cfg.AGENT_OFFLINE_SECONDS