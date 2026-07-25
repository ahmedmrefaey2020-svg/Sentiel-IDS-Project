import secrets
import time
from typing import Optional
from fastapi import Header, HTTPException, Query, status
from backend.dataBase.database import SessionLocal, get_settings_db


_token_cache: dict = {"token": None, "ts": 0.0}
_TOKEN_CACHE_TTL = 15.0


def _get_api_token() -> str:
    now = time.monotonic()
    if _token_cache["token"] is None or (now - _token_cache["ts"]) > _TOKEN_CACHE_TTL:
        db = SessionLocal()
        try:
            s = get_settings_db(db)
            _token_cache["token"] = (s.api_key or "").strip()
            _token_cache["ts"] = now
        finally:
            db.close()
    return _token_cache["token"] or ""


def invalidate_token_cache():
    _token_cache["token"] = None
    _token_cache["ts"] = 0.0


def _assert_token_match(provided: str, stored: str):
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key not configured on server.",
        )
    if not provided or not secrets.compare_digest(provided, stored):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication token.",
        )


async def verify_agent_token(
    token: Optional[str] = Header(None, alias="token"),
    token_query: Optional[str] = Query(None, alias="token"),
) -> str:
    provided = (token or token_query or "").strip()
    stored = _get_api_token()
    _assert_token_match(provided, stored)
    return provided


async def verify_api_agent_mode(
    token: Optional[str] = Header(None, alias="token"),
) -> str:
    stored_key = _get_api_token()
    if not stored_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Server is not in API Agent mode. Configure an API token in settings.",
        )

    provided = (token or "").strip()
    _assert_token_match(provided, stored_key)
    return provided
