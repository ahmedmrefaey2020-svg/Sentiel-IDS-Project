from fastapi import Request
from fastapi.templating import Jinja2Templates
from backend.dataBase.database import get_settings_db, SessionLocal
from backend.dataBase.models import SystemSetting
from backend.handlers.prediction_handler import _apply_batch_results 
from backend.handlers.stats_handler import get_stats

templates = Jinja2Templates(directory="templates")

def _make_handler(template_name: str):
    async def handler(request: Request):
        db = SessionLocal()
        try:
            user = db.query(SystemSetting.org_name).first()
            user = user[0] if user else "Admin"
            
            setting_conf = db.query(SystemSetting.confidence_threshold).first()
            default_confidence = setting_conf[0] if setting_conf else 85.0
        finally:
            db.close()
        
        stats = get_stats()
        recent_flows = stats.get("recent_flows", [])
        
        total_duration = sum(f.get("flow_duration", 0) for f in recent_flows)
        flow_duration = round(total_duration / len(recent_flows), 2) if recent_flows else 0.0
        
        total_bytes = sum(f.get("byte_count", 0) for f in recent_flows)
        byte_count = total_bytes
        
        inbound_bytes = sum(f.get("inbound_bytes", 0) or f.get("bytes_in", 0) for f in recent_flows)
        outbound_bytes = sum(f.get("outbound_bytes", 0) or f.get("bytes_out", 0) for f in recent_flows)
        
        if inbound_bytes == 0 and outbound_bytes == 0 and recent_flows:
            inbound_bytes = sum(f.get("byte_count", 0) for f in recent_flows if f.get("direction") == "inbound")
            outbound_bytes = sum(f.get("byte_count", 0) for f in recent_flows if f.get("direction") == "outbound")
            if inbound_bytes == 0 and outbound_bytes == 0:
                inbound_bytes = stats.get("inbound_bytes", 0)
                outbound_bytes = stats.get("outbound_bytes", 0)

        total_dropped = sum(f.get("dropped_packets", 0) or f.get("packet_drops", 0) for f in recent_flows)
        dropped_packets = total_dropped if total_dropped > 0 else stats.get("dropped_packets", 0)
        
        active_iocs = sum(f.get("active_iocs", 0) for f in recent_flows)
        if active_iocs == 0:
            active_iocs = stats.get("active_iocs", len([f for f in recent_flows if f.get("is_ioc") or f.get("has_ioc")]))
            
        malicious_blocked = sum(f.get("malicious_blocked", 0) for f in recent_flows)
        if malicious_blocked == 0:
            malicious_blocked = stats.get("malicious_blocked", len([f for f in recent_flows if f.get("status") == "blocked" or f.get("blocked")]))
            
        targeted_attacks = stats.get("targeted_attacks", 0)

        dest_port_div = {}
        for f in recent_flows:
            port = f.get("dest_port") or f.get("dport")
            if port is not None:
                dest_port_div[port] = dest_port_div.get(port, 0) + 1
        dest_port_diversity = len(dest_port_div)

        syn_packet_count = sum(f.get("syn_packets", 0) or f.get("syn_count", 0) for f in recent_flows)
        if syn_packet_count == 0:
            syn_packet_count = stats.get("syn_packet_count", stats.get("syn_count", 0))

        ack_packet_count = sum(f.get("ack_packets", 0) or f.get("ack_count", 0) for f in recent_flows)
        if ack_packet_count == 0:
            ack_packet_count = stats.get("ack_packet_count", stats.get("ack_count", 0))

        total_packets = sum(f.get("packet_count", 0) or f.get("packets", 0) for f in recent_flows)
        packet_rate = stats.get("packet_rate", 0)
        if packet_rate == 0 and total_duration > 0:
            packet_rate = round(total_packets / (total_duration / 1000.0), 2)

        syn_rate = stats.get("syn_rate", 0)
        if syn_rate == 0 and total_duration > 0:
            syn_rate = round(syn_packet_count / (total_duration / 1000.0), 2)

        ack_rate = stats.get("ack_rate", 0)
        if ack_rate == 0 and total_duration > 0:
            ack_rate = round(ack_packet_count / (total_duration / 1000.0), 2)
                
        prev_conn = getattr(handler, "_prev_connections", stats.get("connections", 0))
        prev_duration = getattr(handler, "_prev_duration", flow_duration)
        prev_bytes = getattr(handler, "_prev_bytes", byte_count)
        prev_dropped = getattr(handler, "_prev_dropped", dropped_packets)
        prev_inbound = getattr(handler, "_prev_inbound", inbound_bytes)
        prev_outbound = getattr(handler, "_prev_outbound", outbound_bytes)
        prev_iocs = getattr(handler, "_prev_iocs", active_iocs)
        prev_blocked = getattr(handler, "_prev_blocked", malicious_blocked)
        prev_targeted = getattr(handler, "_prev_targeted", targeted_attacks)
        prev_syn_rate = getattr(handler, "_prev_syn_rate", syn_rate)
        prev_packet_rate = getattr(handler, "_prev_packet_rate", packet_rate)
        prev_syn_count = getattr(handler, "_prev_syn_count", syn_packet_count)
        prev_port_div = getattr(handler, "_prev_port_div", dest_port_diversity)
        prev_ack_rate = getattr(handler, "_prev_ack_rate", ack_rate)
        
        def calc_change(curr, prev):
            if not prev or prev == 0:
                return 100.0 if curr > 0 else 0.0
            return round(((curr - prev) / prev) * 100, 2)
            
        connections = stats.get("connections", 0)
        is_anomaly = stats.get("is_anomaly", False)
        message = stats.get("message", "")
        
        conn_change = calc_change(connections, prev_conn)
        duration_change = calc_change(flow_duration, prev_duration)
        byte_change = calc_change(byte_count, prev_bytes)
        dropped_change = calc_change(dropped_packets, prev_dropped)
        inbound_change = calc_change(inbound_bytes, prev_inbound)
        outbound_change = calc_change(outbound_bytes, prev_outbound)
        iocs_change = calc_change(active_iocs, prev_iocs)
        blocked_change = calc_change(malicious_blocked, prev_blocked)
        targeted_change = calc_change(targeted_attacks, prev_targeted)
        syn_rate_change = calc_change(syn_rate, prev_syn_rate)
        packet_rate_change = calc_change(packet_rate, prev_packet_rate)
        syn_count_change = calc_change(syn_packet_count, prev_syn_count)
        port_div_change = calc_change(dest_port_diversity, prev_port_div)
        ack_rate_change = calc_change(ack_rate, prev_ack_rate)
        
        handler._prev_connections = connections
        handler._prev_duration = flow_duration
        handler._prev_bytes = byte_count
        handler._prev_dropped = dropped_packets
        handler._prev_inbound = inbound_bytes
        handler._prev_outbound = outbound_bytes
        handler._prev_iocs = active_iocs
        handler._prev_blocked = malicious_blocked
        handler._prev_targeted = targeted_attacks
        handler._prev_syn_rate = syn_rate
        handler._prev_packet_rate = packet_rate
        handler._prev_syn_count = syn_packet_count
        handler._prev_port_div = dest_port_diversity
        handler._prev_ack_rate = ack_rate
        
        mapping = {"rf": "Random Forest", "ml": "Random Forest", "lstm": "LSTM"}
        model_key = stats.get("model", "lstm")
        model = mapping.get(model_key, "LSTM")
        
        anomaly_flows = [f for f in recent_flows if f.get("status") == "anomaly"] if recent_flows else []
        
        if anomaly_flows:
            con = round(max(f.get("confidence", 0.0) or (f.get("score", 0.0) * 100) for f in anomaly_flows), 2)
            anomaly_ratio = len(anomaly_flows) / len(recent_flows) if recent_flows else 0.0
            
            base_risk = (con * 0.75) + (anomaly_ratio * 100 * 0.25)
            
            if is_anomaly:
                risk_score = round(max(con, base_risk), 2)
            else:
                risk_score = round(base_risk, 2)
                
            risk_score = min(max(risk_score, 0.0), 100.0)
        else:
            con = default_confidence
            risk_score = float(stats.get("score", 0.0))

        return templates.TemplateResponse(
            name=template_name,
            request=request,
            context={
                'user': user,
                'confidence': con,
                'risk_score': risk_score,
                'connections': connections,
                'connections_change': conn_change,
                'flow_duration': flow_duration,
                'flow_duration_change': duration_change,
                'byte_count': byte_count,
                'byte_count_change': byte_change,
                'inbound_bytes': inbound_bytes,
                'inbound_bytes_change': inbound_change,
                'outbound_bytes': outbound_bytes,
                'outbound_bytes_change': outbound_change,
                'dropped_packets': dropped_packets,
                'dropped_packets_change': dropped_change,
                'active_iocs': active_iocs,
                'active_iocs_change': iocs_change,
                'malicious_blocked': malicious_blocked,
                'malicious_blocked_change': blocked_change,
                'targeted_attacks': targeted_attacks,
                'targeted_attacks_change': targeted_change,
                'dest_port_div': dest_port_div,
                'dest_port_diversity': dest_port_diversity,
                'dest_port_diversity_change': port_div_change,
                'packet_rate': packet_rate,
                'packet_rate_change': packet_rate_change,
                'syn_rate': syn_rate,
                'syn_rate_change': syn_rate_change,
                'ack_rate': ack_rate,
                'ack_rate_change': ack_rate_change,
                'syn_packet_count': syn_packet_count,
                'syn_packet_count_change': syn_count_change,
                'is_anomaly': is_anomaly,
                'message': message,
                'recent_flows': recent_flows,
                'model': model
            }
        )
    return handler