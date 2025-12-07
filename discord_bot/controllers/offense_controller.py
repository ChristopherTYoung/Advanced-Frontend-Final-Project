from fastapi import APIRouter, Request, HTTPException
from services.auth_service import auth_service
from services.bot_service import bot_service

router = APIRouter()


@router.get("/api/guilds/{guild_id}/offenses")
async def get_guild_offenses(guild_id: str, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    user_guilds = await auth_service.get_user_guilds(access_token)
    user_guild_ids = {str(g.get("id")) for g in user_guilds}

    if str(guild_id) not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    if not bot_service.offense_service:
        return {"offenses": []}

    offenses = await bot_service.offense_service.get_offenses(guild_id, limit=100)

    import base64

    for offense in offenses:
        if offense.get("picture"):
            offense["picture"] = base64.b64encode(offense["picture"]).decode("utf-8")
        if offense.get("time_of_offense"):
            offense["time_of_offense"] = offense["time_of_offense"].isoformat()
            del offense["time_of_offense"]

    return {"offenses": offenses}
