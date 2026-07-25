from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class BlockedIP(Base):
    __tablename__ = "blocked_ips"
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, unique=True, index=True, nullable=False)
    protocol = Column(String, nullable=False)
    port = Column(Integer, nullable=False, default=0)
    src_bytes = Column(Float, nullable=False, default=0.0)
    blocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class NetworkFlow(Base):
    __tablename__ = "network_flows"
    id = Column(Integer, primary_key=True, index=True)
    time = Column(String, nullable=False)
    src = Column(String, nullable=False, index=True)
    dest = Column(String, nullable=False)
    proto = Column(String, nullable=False)
    duration = Column(String, default="0.0")
    packets = Column(Integer, default=1)
    is_attack = Column(Boolean, default=False, nullable=False)
    label = Column(String, nullable=False, default="Normal")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    org_name = Column(String, default="Sentinel IDS")
    admin_email = Column(String, default="admin@network.local")
    timezone = Column(String, default="UTC")
    push_notifications = Column(Boolean, default=True)
    email_alerts = Column(Boolean, default=True)
    auto_block = Column(Boolean, default=False)
    active_model = Column(String, default="lstm")
    confidence_threshold = Column(Integer, default=85)
    monitoring_mode = Column(String, default="scapy")
    api_key = Column(String, default="")