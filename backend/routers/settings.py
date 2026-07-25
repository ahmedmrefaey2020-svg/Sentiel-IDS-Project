from fastapi import APIRouter, Request
from backend.dataBase.database import get_settings_db, SessionLocal, invalidate_settings_cache
from backend.security import invalidate_token_cache
from backend.dataBase.schemas import SettingsSchema
from backend.dataBase.config import get_settings
from backend.rate_limit import limiter

_cfg = get_settings()
router = APIRouter(prefix="/api", tags=["settings"])


def _mask_token(token: str) -> str:
    if not token:
        return ""
    if len(token) <= 8:
        return "*" * len(token)
    return f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"


@router.post("/update-settings")
@limiter.limit(_cfg.API_RATE_LIMIT_SETTINGS)
async def update_settings(request: Request, settings: SettingsSchema):
    db = SessionLocal()
    try:
        db_settings = get_settings_db(db)
        db_settings.org_name = settings.orgName
        db_settings.admin_email = settings.adminEmail
        db_settings.timezone = settings.timezone
        db_settings.push_notifications = settings.pushNotifications
        db_settings.email_alerts = settings.emailAlerts
        db_settings.auto_block = settings.autoBlock
        db_settings.active_model = settings.activeModel
        db_settings.confidence_threshold = settings.confidence
        db_settings.api_key = settings.token
        db_settings.monitoring_mode = settings.monitoringMode
        db.commit()
    finally:
        db.close()

    invalidate_settings_cache()
    invalidate_token_cache()

    return {
        "status": "success",
        "monitoringMode": settings.monitoringMode,
        "hasToken": bool(settings.token),
    }


@router.get("/get-settings")
async def get_settings_endpoint():
    db = SessionLocal()
    try:
        db_settings = get_settings_db(db)
        token = (db_settings.api_key or "").strip()
        mode = "api_agent" if token else "scapy"
        return {
            "orgName": db_settings.org_name,
            "adminEmail": db_settings.admin_email,
            "timezone": db_settings.timezone,
            "pushNotifications": db_settings.push_notifications,
            "emailAlerts": db_settings.email_alerts,
            "autoBlock": db_settings.auto_block,
            "activeModel": "rf" if db_settings.active_model == "ml" else db_settings.active_model,
            "confidence": db_settings.confidence_threshold,
            "token": token,
            "tokenPreview": _mask_token(token),
            "monitoringMode": mode,
            "hasToken": bool(token),
        }
    finally:
        db.close()
