from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from services.auth_service import auth_service
from services.bot_service import bot_service

router = APIRouter()


@router.get("/api/guilds")
async def api_guilds(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token in session")

    user_guilds = await auth_service.get_user_guilds(access_token)

    if not bot_service.is_ready():
        print("DEBUG: Bot is not ready, returning empty list")
        return JSONResponse({"guilds": []})

    bot_guilds = bot_service.get_guilds()
    bot_guild_ids = {g["id"] for g in bot_guilds}

    available_guilds = [
        {
            "id": guild["id"],
            "name": guild["name"],
            "icon": guild.get("icon"),
            "owner": guild.get("owner", False),
            "permissions": guild.get("permissions"),
        }
        for guild in user_guilds
        if guild["id"] in bot_guild_ids
    ]

    print(f"DEBUG /api/guilds: Returning {len(available_guilds)} guilds")
    for g in available_guilds:
        print(f"  - {g['name']} (owner={g.get('owner')})")

    return JSONResponse({"guilds": available_guilds})
