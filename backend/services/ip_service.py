import asyncio
import time
from backend.dataBase.database import SessionLocal
from backend.dataBase.models import BlockedIP
from backend.dataBase.config import get_settings

_cfg = get_settings()

_blocked_ips_cache: set[str] = set()
_cache_ts: float = 0.0
_cache_lock = asyncio.Lock()
CACHE_TTL = float(_cfg.BLOCKED_IP_CACHE_TTL)


async def _refresh_cache_if_stale():
    global _cache_ts
    now = time.monotonic()
    if (now - _cache_ts) < CACHE_TTL:
        return
    loop = asyncio.get_running_loop()
    ips = await loop.run_in_executor(None, _load_blocked_ips_from_db)
    async with _cache_lock:
        _blocked_ips_cache.clear()
        _blocked_ips_cache.update(ips)
        _cache_ts = now


def _load_blocked_ips_from_db() -> set[str]:
    db = SessionLocal()
    try:
        rows = db.query(BlockedIP.ip_address).all()
        return {r[0] for r in rows}
    finally:
        db.close()


def _sync_add_to_db(ip: str, protocol: str, port: int, src_bytes: float) -> bool:
    db = SessionLocal()
    try:
        existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
        if existing:
            return False
        db.add(BlockedIP(ip_address=ip, protocol=protocol, port=port, src_bytes=src_bytes))
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


async def is_ip_blocked(ip: str) -> bool:
    await _refresh_cache_if_stale()
    return ip in _blocked_ips_cache


async def block_ip(ip: str, protocol: str, port: int, src_bytes: float) -> bool:
    if ip in _blocked_ips_cache:
        return False

    loop = asyncio.get_running_loop()
    added = await loop.run_in_executor(None, _sync_add_to_db, ip, protocol, port, src_bytes)

    if added:
        async with _cache_lock:
            _blocked_ips_cache.add(ip)

    return added


def sync_block_ip(ip: str, protocol: str, port: int, src_bytes: float) -> bool:
    if ip in _blocked_ips_cache:
        return False
    added = _sync_add_to_db(ip, protocol, port, src_bytes)
    if added:
        _blocked_ips_cache.add(ip)
    return added


def is_ip_blocked_sync(ip: str) -> bool:
    return ip in _blocked_ips_cache


async def unblock_ip(ip: str) -> bool:
    loop = asyncio.get_running_loop()
    removed = await loop.run_in_executor(None, _sync_remove_from_db, ip)
    if removed:
        async with _cache_lock:
            _blocked_ips_cache.discard(ip)
    return removed


def _sync_remove_from_db(ip: str) -> bool:
    db = SessionLocal()
    try:
        row = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()
