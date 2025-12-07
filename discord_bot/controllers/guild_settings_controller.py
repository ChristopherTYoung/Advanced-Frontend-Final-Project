import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from services.auth_service import auth_service
from services.settings_service import settings_service
from services.bot_service import bot_service
from services.llm_service import llm_service

from schemas import UpdateSettingsRequest, ContentMaturityPreferences

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
    user_guild_ids = {str(g.get("id")) for g in user_guilds}

    if str(guild_id) not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    settings = await settings_service.get_settings(guild_id)

    if settings:
        s = settings.get("settings") if isinstance(settings, dict) else settings
        return JSONResponse(settings)
    else:
        return JSONResponse(
            {"guild_id": guild_id, "settings": {"bot_settings": {}, "role_settings": {"roles": []}}, "edited_at": None}
        )


@router.post("/api/guilds/{guild_id}/settings")
async def api_update_guild_settings(guild_id: str, payload: UpdateSettingsRequest, request: Request):
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

    if not settings_service:
        raise HTTPException(status_code=503, detail="Settings service not available")

    old_settings = await settings_service.get_settings(guild_id)
    old_nickname = None
    if old_settings and isinstance(old_settings, dict):
        settings_obj = old_settings.get("settings") or {}
        bot_settings = settings_obj.get("bot_settings") if isinstance(settings_obj, dict) else None
        if bot_settings and isinstance(bot_settings, dict):
            old_nickname = bot_settings.get("bot_nickname")
        else:
            old_nickname = settings_obj.get("bot_nickname")

    settings_dict = payload.settings.model_dump(exclude_none=True)
    bot_settings = settings_dict.get("bot_settings", {})
    new_nickname = bot_settings.get("bot_nickname")

    if "role_settings" in settings_dict and settings_dict.get("role_settings") is not None:
        guild_entry = next((g for g in user_guilds if str(g.get("id")) == str(guild_id)), None)
        is_guild_owner = False
        if guild_entry:
            print(f"DEBUG: guild_entry for {guild_id}: {guild_entry}")
            owner_value = guild_entry.get("owner")
            print(f"DEBUG: owner value: {owner_value}, type: {type(owner_value)}")
            if guild_entry.get("owner"):
                is_guild_owner = True
        else:
            print(f"DEBUG: No guild_entry found for guild_id {guild_id}")
            print(f"DEBUG: Available guild IDs: {[str(g.get('id')) for g in user_guilds]}")

        if not is_guild_owner:
            print(f"DEBUG: Blocked role_settings update for guild {guild_id}. is_guild_owner={is_guild_owner}")
            raise HTTPException(status_code=403, detail="Only the guild owner may modify role settings")

    success = await settings_service.update_settings(guild_id, settings_dict)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update settings")

    if new_nickname and new_nickname != old_nickname:
        asyncio.create_task(bot_service.announce_nickname_change(guild_id, old_nickname, new_nickname))

    return JSONResponse(
        {
            "ok": True,
            "message": "Settings updated successfully",
            "guild_id": guild_id,
            "settings": settings_dict,
        }
    )


@router.delete("/api/guilds/{guild_id}/settings")
async def api_delete_guild_settings(guild_id: str, request: Request):
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

    success = await settings_service.delete_settings(guild_id)

    if success:
        return JSONResponse({"ok": True, "message": "Settings deleted successfully", "guild_id": guild_id})
    else:
        raise HTTPException(status_code=500, detail="Failed to delete settings")


# Roles will already have some permissions via discord
# Do we check for those to?
# We will need separate permissions for managing the bot
@router.get("/api/guilds/{guild_id}/roles")
async def api_get_guild_roles(guild_id: str, request: Request):
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

    user_guild_ids = {str(g.get("id")) for g in user_guilds}
    if str(guild_id) not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    if not bot_service.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready")

    guild = bot_service.get_guild_by_id(int(guild_id))
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found or bot not in guild")

    roles_list = []
    for role in guild.roles:
        roles_list.append(
            {
                "id": str(role.id),
                "name": role.name,
                "mentionable": bool(getattr(role, "mentionable", False)),
                "hoist": bool(getattr(role, "hoist", False)),
                "managed": bool(getattr(role, "managed", False)),
                "position": int(getattr(role, "position", 0)),
            }
        )

    return JSONResponse({"roles": roles_list})


@router.get("/api/guilds/{guild_id}/user/permissions")
async def api_get_user_permissions(guild_id: str, request: Request):
    """Get the current user's permissions for a guild based on their roles."""
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

    user_guild_ids = {str(g.get("id")) for g in user_guilds}
    if str(guild_id) not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    guild_entry = next((g for g in user_guilds if str(g.get("id")) == str(guild_id)), None)
    is_owner = guild_entry.get("owner", False) if guild_entry else False

    if is_owner:
        return JSONResponse(
            {
                "is_owner": True,
                "permissions": {
                    "change_nickname": True,
                    "change_personality": True,
                    "make_events": True,
                    "manage_proposals": True,
                },
                "user_roles": [],
            }
        )

    if not bot_service.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready")

    guild = bot_service.get_guild_by_id(int(guild_id))
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found or bot not in guild")

    user_id = int(user.get("id"))
    member = guild.get_member(user_id)

    if not member:
        try:
            member = await guild.fetch_member(user_id)
            print(f"DEBUG: Fetched member {user_id} from guild {guild_id}")
        except Exception as e:
            print(f"DEBUG: Could not fetch member {user_id}: {e}")

    if not member:
        print(f"DEBUG: Member {user_id} not found in guild {guild_id}")
        return JSONResponse(
            {
                "is_owner": False,
                "permissions": {
                    "change_nickname": False,
                    "change_personality": False,
                    "make_events": False,
                    "manage_proposals": False,
                },
                "user_roles": [],
            }
        )

    user_role_ids = [str(role.id) for role in member.roles]
    print(f"DEBUG: User {user_id} has roles: {user_role_ids}")

    settings = await settings_service.get_settings(guild_id)
    role_settings = []
    if settings and isinstance(settings, dict):
        settings_obj = settings.get("settings") or {}
        if isinstance(settings_obj, dict):
            role_settings_data = settings_obj.get("role_settings") or {}
            if isinstance(role_settings_data, dict):
                role_settings = role_settings_data.get("roles") or []

    print(f"DEBUG: Found {len(role_settings)} role configurations")

    permissions = {
        "change_nickname": False,
        "change_personality": False,
        "make_events": False,
        "manage_proposals": False,
    }

    for role_config in role_settings:
        role_id = role_config.get("role_id")
        role_name = role_config.get("role_name", "unknown")
        if role_id and role_id in user_role_ids:
            print(f"DEBUG: User has matching role: {role_name} ({role_id})")
            for perm in role_config.get("permissions", []):
                perm_name = perm.get("permission_name")
                perm_allowed = perm.get("allowed", False)
                if perm_name in permissions and perm_allowed:
                    permissions[perm_name] = True
                    print(f"DEBUG: Granted permission {perm_name} from role {role_name}")

    print(f"DEBUG: Final permissions: {permissions}")

    return JSONResponse({"is_owner": False, "permissions": permissions, "user_roles": user_role_ids})


@router.get("/api/guilds/{guild_id}/maturity-preferences")
async def api_get_maturity_preferences(guild_id: str, request: Request):
    """Get content maturity preferences for a guild."""
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

    settings = await settings_service.get_settings(guild_id)

    if settings and isinstance(settings, dict):
        settings_obj = settings.get("settings") or {}
        if isinstance(settings_obj, dict):
            maturity_prefs = settings_obj.get("content_maturity_preferences") or {}
            return JSONResponse({"guild_id": guild_id, "content_maturity_preferences": maturity_prefs})

    return JSONResponse({"guild_id": guild_id, "content_maturity_preferences": {}})


@router.post("/api/guilds/{guild_id}/maturity-preferences")
async def api_update_maturity_preferences(guild_id: str, preferences: ContentMaturityPreferences, request: Request):
    """Update content maturity preferences for a guild. Only guild owner can modify."""
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

    # Check if user is owner - only owners can modify maturity preferences
    guild_entry = next((g for g in user_guilds if str(g.get("id")) == str(guild_id)), None)
    is_owner = guild_entry.get("owner", False) if guild_entry else False

    if not is_owner:
        print(f"DEBUG: Blocked maturity preferences update for guild {guild_id}. User is not owner.")
        raise HTTPException(status_code=403, detail="Only the guild owner may modify content maturity preferences")

    # Get existing settings
    existing_settings = await settings_service.get_settings(guild_id)

    settings_dict = {}
    if existing_settings and isinstance(existing_settings, dict):
        settings_obj = existing_settings.get("settings") or {}
        if isinstance(settings_obj, dict):
            settings_dict = {
                "bot_settings": settings_obj.get("bot_settings"),
                "role_settings": settings_obj.get("role_settings"),
                "content_maturity_preferences": preferences.model_dump(exclude_none=True),
            }
    else:
        settings_dict = {"content_maturity_preferences": preferences.model_dump(exclude_none=True)}

    success = await settings_service.update_settings(guild_id, settings_dict)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update maturity preferences")

    return JSONResponse(
        {
            "ok": True,
            "message": "Content maturity preferences updated successfully",
            "guild_id": guild_id,
            "content_maturity_preferences": preferences.model_dump(exclude_none=True),
        }
    )
