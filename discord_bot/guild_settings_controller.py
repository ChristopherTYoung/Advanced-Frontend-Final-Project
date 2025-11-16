import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from services.auth_service import auth_service
from services.settings_service import settings_service
from services.bot_service import bot_service
from services.llm_service import llm_service

from schemas import UpdateSettingsRequest

router = APIRouter()

@router.get("/api/guilds/{guild_id}/settings")
async def api_get_guild_settings(guild_id: str, request: Request):
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

    settings = await settings_service.get_settings(guild_id)
    
    if settings:
        return JSONResponse(settings)
    else:
        return JSONResponse({
            "guild_id": guild_id,
            "settings": {},
            "edited_at": None
        })


@router.post("/api/guilds/{guild_id}/settings")
async def api_update_guild_settings(guild_id: str, payload: UpdateSettingsRequest, request: Request):
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

    if not settings_service:
        raise HTTPException(status_code=503, detail="Settings service not available")

    old_settings = await settings_service.get_settings(guild_id)
    old_nickname = old_settings.get("settings", {}).get("bot_nickname") if old_settings else None
    
    settings_dict = payload.settings.model_dump(exclude_none=True)
    new_nickname = settings_dict.get("bot_nickname")
    
    success = await settings_service.update_settings(guild_id, settings_dict)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update settings")

    try:
        if new_nickname and new_nickname != old_nickname:
            asyncio.create_task(bot_service.announce_nickname_change(guild_id, old_nickname, new_nickname))
    except Exception as e:
        print(f"ERROR scheduling nickname announcement: {e}")

    return JSONResponse({
        "ok": True,
        "message": "Settings updated successfully",
        "guild_id": guild_id
    })


@router.delete("/api/guilds/{guild_id}/settings")
async def api_delete_guild_settings(guild_id: str, request: Request):
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

    success = await settings_service.delete_settings(guild_id)
    
    if success:
        return JSONResponse({
            "ok": True,
            "message": "Settings deleted successfully",
            "guild_id": guild_id
        })
    else:
        raise HTTPException(status_code=500, detail="Failed to delete settings")
