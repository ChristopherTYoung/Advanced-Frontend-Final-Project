from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from services.message_service import message_service

router = APIRouter()


@router.get("/api/messages")
async def api_get_messages(request: Request, limit: int = 50, message_type: str = None):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    limit = min(limit, 100)

    messages = await message_service.get_history(limit=limit, message_type=message_type)

    return JSONResponse({"messages": messages})


@router.get("/api/messages/dm")
async def api_get_dm_messages(request: Request, limit: int = 50):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    limit = min(limit, 100)

    messages = await message_service.get_dm_messages(limit=limit)

    return JSONResponse({"messages": messages})
