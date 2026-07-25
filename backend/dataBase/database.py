from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from backend.dataBase.models import Base, SystemSetting, BlockedIP
from backend.dataBase.config import get_settings
import time

_cfg = get_settings()

engine = create_engine(
    _cfg.DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 20},
    poolclass=StaticPool,
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

_settings_cache: dict = {"data": None, "ts": 0.0}
_cfg_cache_ttl = _cfg.SETTINGS_CACHE_TTL


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_settings_db(db: Session) -> SystemSetting:
    settings = db.query(SystemSetting).first()
    if not settings:
        settings = SystemSetting(
            org_name="Sentinel IDS",
            admin_email="admin@network.local",
            timezone="UTC",
            push_notifications=True,
            email_alerts=True,
            auto_block=False,
            active_model="lstm",
            confidence_threshold=85,
            monitoring_mode="scapy",
            api_key="",
        )
        db.add(settings)
        try:
            db.commit()
            db.refresh(settings)
        except Exception:
            db.rollback()
            raise
    return settings


def get_cached_monitoring_config() -> tuple[str, str, int, bool]:
    now = time.monotonic()
    if _settings_cache["data"] is None or (now - _settings_cache["ts"]) > _cfg_cache_ttl:
        db = SessionLocal()
        try:
            s = get_settings_db(db)
            has_token = bool((s.api_key or "").strip())
            mode = "api_agent" if has_token else "scapy"
            model = "rf" if s.active_model == "ml" else (s.active_model or "lstm")
            _settings_cache["data"] = (
                mode,
                model,
                int(s.confidence_threshold or 85),
                bool(s.auto_block),
            )
            _settings_cache["ts"] = now
        finally:
            db.close()
    return _settings_cache["data"]


def invalidate_settings_cache():
    _settings_cache["data"] = None
    _settings_cache["ts"] = 0.0


def get_latest_network_stats(model_type: str = "lstm") -> dict:
    from backend.handlers.stats_handler import get_stats

    current_stats = get_stats()

    db = SessionLocal()
    try:
        total_blocked = db.query(BlockedIP).count()
        recent_blocks = db.query(BlockedIP).order_by(BlockedIP.id.desc()).limit(20).all()
        blocked_list = [
            {
                "time": b.blocked_at.strftime("%H:%M:%S") if b.blocked_at else "N/A",
                "src": b.ip_address,
                "port": b.port,
                "proto": b.protocol,
                "status": "anomaly",
            }
            for b in recent_blocks
        ]
    finally:
        db.close()

    flows = current_stats.get("recent_flows", [])
    anomaly_flows = [f for f in flows if f.get("status") == "anomaly"]

    return {
        "active_connections": current_stats["connections"],
        "packet_rate": current_stats["packet_rate"],
        "risk_score": current_stats["score"],
        "risk_message": current_stats["message"],
        "is_anomaly": current_stats["is_anomaly"],
        "network_flows": flows,
        "recent_flows": flows,
        "blocked_list": blocked_list,
        "total_blocked": total_blocked,
        "total_iocs": len(anomaly_flows) + total_blocked,
    }
