import io
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from backend.security import verify_agent_token

router = APIRouter(prefix="/api", tags=["agent"])

_AGENT_TEMPLATE_PATH = "backend/agent_template.py"


@router.get("/download-agent")
async def download_agent(
    request: Request,
    _token: str = Depends(verify_agent_token),
):
    base_url = str(request.base_url).rstrip("/")
    with open(_AGENT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("REPLACE_WITH_USER_TOKEN", _token)
    content = content.replace("REPLACE_WITH_YOUR_SITE_URL", base_url)

    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="text/x-python",
        headers={"Content-Disposition": "attachment; filename=sentinel_agent.py"},
    )
