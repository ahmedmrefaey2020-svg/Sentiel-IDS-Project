from collections import deque


FEATURE_NAMES = [
    "Flow Duration", "Flow IAT Mean", "Flow IAT Max", "Flow IAT Min",
    "TotLen Fwd Pkts", "TotLen Bwd Pkts", "Fwd Pkt Len Max", "Fwd Pkt Len Mean",
    "Bwd Pkt Len Max", "Bwd Pkt Len Mean", "Pkt Size Avg",
    "FIN Flag Cnt", "SYN Flag Cnt", "RST Flag Cnt", "PSH Flag Cnt",
    "ACK Flag Cnt", "URG Flag Cnt",
    "Init Fwd Win Byts", "Init Bwd Win Byts",
    "Flow Byts/s", "Flow Pkts/s",
    "Fwd Pkt Len Std", "Pkt Len Var", "Fwd Header Len",
]

NUM_FEATURES = len(FEATURE_NAMES)


def extract_features(payload_data: dict) -> list[float]:
    return [float(payload_data.get(k, 0.0)) for k in FEATURE_NAMES]


def compute_dynamic_xai(data: dict, active_model: str) -> dict:
    is_anomaly = data.get("is_anomaly", False)
    risk_score = data.get("risk_score", 10)
    flows = data.get("network_flows") or data.get("recent_flows") or []

    tcp_count = sum(1 for f in flows if str(f.get("proto", "")).upper() == "TCP")
    total_flows = len(flows) or 1

    syn_val = round((tcp_count / total_flows) * (25.5 if is_anomaly else 2.5), 1)
    byte_val = round(risk_score * 0.2, 1)
    ack_val = round(-10.5 if is_anomaly else -0.5, 1)

    return {
        "title": "DDoS Attack Expected" if is_anomaly else "Normal Traffic Patterns",
        "confidence": min(99, max(50, risk_score + 5)) if is_anomaly else min(30, max(5, risk_score)),
        "target_ip": flows[0]["src"] if flows else "N/A",
        "model_name": "LSTM (v2.4)" if active_model == "lstm" else "Random Forest (v1.2)",
        "features": [
            {"name": "SYN Rate", "value": syn_val},
            {"name": "Byte Count", "value": byte_val},
            {"name": "ACK Rate", "value": ack_val},
        ],
    }
