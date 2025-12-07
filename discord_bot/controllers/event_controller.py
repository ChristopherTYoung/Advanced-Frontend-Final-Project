from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from services.auth_service import auth_service
from services.event_service import event_service
from schemas import EventCreateRequest


router = APIRouter()


def _user_is_admin(user_guilds: list, guild_id: str) -> bool:
    for g in user_guilds:
        if str(g.get("id")) == str(guild_id):
            if g.get("owner"):
                return True
            perms = g.get("permissions")
            try:
                if perms is not None and int(perms) & 0x20:
                    return True
            except Exception:
                pass
    return False


@router.post("/api/guilds/{guild_id}/events")
async def api_create_guild_event(guild_id: str, payload: EventCreateRequest, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    try:
        user_guilds = await auth_service.get_user_guilds(access_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required; please sign in again")
    user_guild_ids = {g["id"] for g in user_guilds}
    if guild_id not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    user_id = user.get("id")
    username = user.get("username")

    event_id = await event_service.create_event(
        guild_id=guild_id,
        user_id=user_id,
        username=username,
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

    try:
        user_guilds = await auth_service.get_user_guilds(access_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required; please sign in again")
    user_guild_ids = {g["id"] for g in user_guilds}
    if guild_id not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    limit = min(limit, 100)
    events = await event_service.list_events(guild_id=guild_id, limit=limit)

    return JSONResponse({"events": events})


@router.post("/api/guilds/{guild_id}/events/{event_id}/cancel")
async def api_cancel_event(guild_id: str, event_id: int, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    user_guilds = await auth_service.get_user_guilds(access_token)
    if not _user_is_admin(user_guilds, guild_id):
        raise HTTPException(status_code=403, detail="Admin permissions required to cancel events")

    canceled = await event_service.cancel_event(event_id)
    if not canceled:
        raise HTTPException(status_code=500, detail="Failed to cancel event")

    return JSONResponse({"ok": True})
