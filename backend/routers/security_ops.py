from fastapi import APIRouter, Request, Depends, status
from backend.dataBase.schemas import BlockIPSchema, ExternalIngestPayload
from backend.security import verify_api_agent_mode
from backend.services.ip_service import block_ip, unblock_ip
from backend.handlers.prediction_handler import ingest_external_batch
from backend.dataBase.database import get_settings_db, SessionLocal
from backend.dataBase.config import get_settings
from backend.rate_limit import limiter

_cfg = get_settings()
router = APIRouter(prefix="/api", tags=["security"])


@router.post("/block-ip", status_code=status.HTTP_200_OK)
@limiter.limit(_cfg.API_RATE_LIMIT_BLOCK)
async def block_ip_endpoint(request: Request, data: BlockIPSchema):
    added = await block_ip(data.ip, "MANUAL", 0, 0.0)
    if added:
        return {"status": "success", "message": f"IP {data.ip} has been blocked."}
    return {"status": "info", "message": "IP already blocked."}


@router.post("/unblock-ip", status_code=status.HTTP_200_OK)
@limiter.limit(_cfg.API_RATE_LIMIT_BLOCK)
async def unblock_ip_endpoint(request: Request, data: BlockIPSchema):
    removed = await unblock_ip(data.ip)
    if removed:
        return {"status": "success", "message": f"IP {data.ip} has been unblocked."}
    return {"status": "info", "message": "IP was not in the blocklist."}


@router.post("/external-data-ingest")
@limiter.limit(_cfg.API_RATE_LIMIT_INGEST)
async def ingest_external_data(
    request: Request,
    payload: ExternalIngestPayload,
    _token: str = Depends(verify_api_agent_mode),
):
    db = SessionLocal()
    try:
        db_settings = get_settings_db(db)
        active_model = "rf" if db_settings.active_model == "ml" else db_settings.active_model
    finally:
        db.close()

    records_features = [r.to_feature_list() for r in payload.records]
    metadata = [r.metadata() for r in payload.records]
    result = ingest_external_batch(records_features, metadata, active_model)
    return {"status": "analyzed", "result": result}
