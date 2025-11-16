from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from services.auth_service import auth_service
from services.event_service import event_service
from schemas import EventCreateRequest

router = APIRouter()

@router.post("/api/guilds/{guild_id}/events")
async def api_create_guild_event(guild_id: str, payload: EventCreateRequest, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    user_guilds = await auth_service.get_user_guilds(access_token)
    user_guild_ids = {g["id"] for g in user_guilds}
    if guild_id not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    user_id = user.get("id")

    event_id = await event_service.create_event(
        guild_id=guild_id,
        user_id=user_id,
        time_of_event=payload.time_of_event,
        event_name=payload.event_name,
        event_details=payload.event_details,
    )

    if event_id is None:
        raise HTTPException(status_code=500, detail="Failed to create event")

    return JSONResponse({"ok": True, "event_id": event_id, "guild_id": guild_id})


@router.get("/api/guilds/{guild_id}/events")
async def api_get_guild_events(guild_id: str, request: Request, limit: int = 50):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    user_guilds = await auth_service.get_user_guilds(access_token)
    user_guild_ids = {g["id"] for g in user_guilds}
    if guild_id not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    limit = min(limit, 100)
    events = await event_service.list_events(guild_id=guild_id, limit=limit)

    return JSONResponse({"events": events})
