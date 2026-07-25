import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.dataBase.database import get_latest_network_stats, get_settings_db, SessionLocal
from backend.xai import compute_dynamic_xai
from backend.ws_manager import manager
from backend.dataBase.models import NetworkFlow
from backend.dataBase.schemas import NetworkFlowOut
from backend.handlers.stats_handler import get_last_external_time, is_agent_offline

router = APIRouter(prefix="/api", tags=["dashboard"])


async def get_dashboard_data():
    db = SessionLocal()
    try:
        db_settings = get_settings_db(db)
        active_model = "rf" if db_settings.active_model == "ml" else db_settings.active_model
        token = (db_settings.api_key or "").strip()
        mode = "api_agent" if token else "scapy"
    finally:
        db.close()

    is_fallback_active = mode == "api_agent" and is_agent_offline()
    data = get_latest_network_stats(model_type=active_model)
    data["monitoring_mode"] = mode
    data["is_fallback_active"] = is_fallback_active
    data["active_model"] = active_model
    data["has_api_token"] = bool(token)
    data["user_api_token"] = token[:8] if token else ""
    data["agent_last_seen"] = get_last_external_time()
    data["xai_explanation"] = compute_dynamic_xai(data, active_model)
    return data


@router.get("/dashboard-data")
async def get_dashboard_data_endpoint():
    return await get_dashboard_data()


@router.get("/dataset-explorer-data", response_model=list[NetworkFlowOut])
async def get_explorer_data():
    loop = asyncio.get_running_loop()

    def _query():
        db = SessionLocal()
        try:
            return db.query(NetworkFlow).order_by(NetworkFlow.id.desc()).limit(500).all()
        finally:
            db.close()

    flows = await loop.run_in_executor(None, _query)
    return flows


@router.websocket("/ws/live-traffic")
async def websocket_live_traffic(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)


async def global_traffic_broadcaster():
    while True:
        await asyncio.sleep(2)
        if manager.active_count > 0:
            try:
                data = await get_dashboard_data()
                await manager.broadcast(data)
            except Exception as e:
                print(f"Error in broadcast loop: {e}")


@router.on_event("startup")
async def startup_event():
    asyncio.create_task(global_traffic_broadcaster())