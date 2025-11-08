"""Main FastAPI application."""

import os
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import discord

from services.bot_service import bot_service
from services.auth_service import auth_service
from services.message_service import message_service
from services.settings_service import settings_service
from services.llm_service import llm_service
from schemas import (
    SendMessageRequest,
    UpdateSettingsRequest,
    SuccessResponse,
    MessageSentResponse,
    SettingsUpdatedResponse,
    SettingsDeletedResponse,
    GuildSettingsResponse,
    MeResponse,
    LogoutResponse,
    GuildsResponse,
    ChannelsResponse,
    MessagesResponse,
    GuildInfo,
    ChannelInfo,
    MessageInfo,
)

app = FastAPI()

# Configuration
SESSION_SECRET = os.environ.get("DISCORD_SESSION_SECRET", "dev-secret-change-me")
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173")
DISCORD_SESSION_SAMESITE = os.environ.get("DISCORD_SESSION_SAMESITE", "lax")
DISCORD_SESSION_HTTPS_ONLY = os.environ.get("DISCORD_SESSION_HTTPS_ONLY", "false").lower() in ("1", "true", "yes")
DATABASE_URL = os.environ.get("DB_CONNECTION_STRING")

# Connect services
bot_service.message_service = message_service
bot_service.settings_service = settings_service
print(f"DEBUG: Services connected")


# Lifecycle Events
@app.on_event("startup")
async def startup_event():
    """Start the Discord bot and initialize database on application startup."""
    print(f"DEBUG: Initializing database pool...")
    await message_service.init_db_pool(DATABASE_URL)
    await settings_service.init_db_pool(DATABASE_URL)
    print(f"DEBUG: Bot service has message_service: {bot_service.message_service is not None}")
    await bot_service.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the Discord bot and close database on application shutdown."""
    await bot_service.stop()
    await message_service.close_db_pool()
    await settings_service.close_db_pool()


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in FRONTEND_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site=DISCORD_SESSION_SAMESITE,
    https_only=DISCORD_SESSION_HTTPS_ONLY,
)


# Routes
@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"hello": "world"}


# Authentication Routes
@app.get("/api/auth/login")
async def auth_login():
    """Redirect to Discord OAuth authorization page."""
    auth_url = auth_service.get_authorization_url()
    return RedirectResponse(url=auth_url)


@app.get("/api/auth/callback")
async def auth_callback(code: Optional[str] = None, request: Request = None):
    """Handle OAuth callback from Discord."""
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")

    access_token = await auth_service.exchange_code_for_token(code)

    request.session["access_token"] = access_token

    user_info = await auth_service.get_user_info(access_token)

    request.session["user"] = user_info

    return RedirectResponse(url=auth_service.get_frontend_redirect_url(success=True))


@app.get("/api/me")
async def api_me(request: Request):
    """Get current user information from session."""
    user = request.session.get("user")
    if not user:
        return JSONResponse({"user": None})
    return JSONResponse({"user": user})


@app.post("/api/logout")
async def api_logout(request: Request):
    """Clear user session."""
    request.session.pop("user", None)
    request.session.pop("access_token", None)
    return JSONResponse({"ok": True})


# Guild Routes
@app.get("/api/guilds")
async def api_guilds(request: Request):
    """Get guilds where the user is a member and the bot is also installed."""
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token in session")

    user_guilds = await auth_service.get_user_guilds(access_token)

    print(f"DEBUG: User has {len(user_guilds)} guilds")
    print(f"DEBUG: User guild IDs: {[g['id'] for g in user_guilds]}")

    if not bot_service.is_ready():
        print("DEBUG: Bot is not ready, returning empty list")
        return JSONResponse({"guilds": []})

    bot_guilds = bot_service.get_guilds()
    bot_guild_ids = {g["id"] for g in bot_guilds}

    print(f"DEBUG: Bot is in {len(bot_guilds)} guilds")
    print(f"DEBUG: Bot guild IDs: {bot_guild_ids}")

    available_guilds = [
        {"id": guild["id"], "name": guild["name"], "icon": guild.get("icon")}
        for guild in user_guilds
        if guild["id"] in bot_guild_ids
    ]

    print(f"DEBUG: Found {len(available_guilds)} matching guilds")

    return JSONResponse({"guilds": available_guilds})


@app.get("/api/guilds/{guild_id}/channels")
async def api_guild_channels(guild_id: str, request: Request):
    """Get text channels for a specific guild."""
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not bot_service.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready")

    # Get the guild from the bot
    guild = bot_service.get_guild_by_id(int(guild_id))
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found or bot is not in this guild")

    # Get text channels
    text_channels = [{"id": str(channel.id), "name": channel.name} for channel in guild.text_channels]

    return JSONResponse({"channels": text_channels})


# Message Routes
@app.post("/api/send-message")
async def api_send_message(payload: SendMessageRequest, request: Request):
    """Send a message to a Discord channel via the bot."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not bot_service.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready")

    try:
        await bot_service.send_message(
            int(payload.channel_id), payload.message, user_id=user.get("id"), username=user.get("username")
        )
        return JSONResponse({"ok": True, "message": "Message sent successfully"})

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except discord.Forbidden:
        raise HTTPException(status_code=403, detail="Bot does not have permission to send messages in this channel")
    except discord.HTTPException as e:
        raise HTTPException(status_code=500, detail=f"Discord API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@app.get("/api/messages")
async def api_get_messages(request: Request, limit: int = 50, message_type: str = None):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Limit the limit :)
    limit = min(limit, 100)

    messages = await message_service.get_history(limit=limit, message_type=message_type)

    return JSONResponse({"messages": messages})


@app.get("/api/messages/dm")
async def api_get_dm_messages(request: Request, limit: int = 50):
    """Get direct messages sent to the bot."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Limit the limit
    limit = min(limit, 100)

    messages = await message_service.get_dm_messages(limit=limit)
    print(f"DEBUG: Returning {len(messages)} DM messages")

    return JSONResponse({"messages": messages})


# Settings Routes
@app.get("/api/guilds/{guild_id}/settings")
async def api_get_guild_settings(guild_id: str, request: Request):
    """Get bot settings for a specific guild."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify user has access to this guild
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    user_guilds = await auth_service.get_user_guilds(access_token)
    user_guild_ids = {g["id"] for g in user_guilds}
    
    if guild_id not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    # Get settings from database
    settings = await settings_service.get_settings(guild_id)
    
    if settings:
        return JSONResponse(settings)
    else:
        # Return default empty settings if none exist
        return JSONResponse({
            "guild_id": guild_id,
            "settings": {},
            "edited_at": None
        })


@app.post("/api/guilds/{guild_id}/settings")
async def api_update_guild_settings(guild_id: str, payload: UpdateSettingsRequest, request: Request):
    """Update bot settings for a specific guild."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify user has access to this guild
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    user_guilds = await auth_service.get_user_guilds(access_token)
    user_guild_ids = {g["id"] for g in user_guilds}
    
    if guild_id not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    # Verify bot is in the guild
    if not bot_service.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready")

    bot_guilds = bot_service.get_guilds()
    bot_guild_ids = {g["id"] for g in bot_guilds}
    
    if guild_id not in bot_guild_ids:
        raise HTTPException(status_code=404, detail="Bot is not in this guild")

    # Get old settings to check if nickname changed
    old_settings = await settings_service.get_settings(guild_id)
    old_nickname = old_settings.get("settings", {}).get("bot_nickname") if old_settings else None
    
    # Convert Pydantic model to dict for storage
    settings_dict = payload.settings.model_dump(exclude_none=True)
    new_nickname = settings_dict.get("bot_nickname")

    # Update settings in database
    success = await settings_service.update_settings(guild_id, settings_dict)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update settings")

    # Check if bot_nickname changed and is not None
    if new_nickname and new_nickname != old_nickname:
        try:
            # Get guild object
            guild = bot_service.get_guild_by_id(int(guild_id))
            if guild:
                # Change bot nickname using the tool call
                nickname_result = await bot_service._tool_change_bot_nickname(guild_id, new_nickname)
                
                if nickname_result.get("success"):
                    # Generate announcement message using LLM
                    prompt = (
                        f"You just changed your nickname to '{new_nickname}' in the Discord server. "
                        f"Generate a short, friendly message announcing your new name. "
                        f"Be creative but concise (1-2 sentences max). "
                        f"Example style: 'Hello everyone! I am now {new_nickname} 😊'"
                    )
                    
                    announcement = await llm_service.generate_response(
                        user_message=prompt,
                        system_prompt="You are a Discord bot announcing your new nickname. Be friendly and concise.",
                        use_tools=False
                    )
                    
                    # Send announcement to the first available text channel
                    if announcement and guild.text_channels:
                        # Find the first channel the bot can send messages to
                        for channel in guild.text_channels:
                            if channel.permissions_for(guild.me).send_messages:
                                await channel.send(announcement)
                                print(f"DEBUG: Sent nickname announcement to #{channel.name}")
                                break
                else:
                    print(f"WARNING: Failed to change bot nickname: {nickname_result.get('error')}")
        except Exception as e:
            print(f"ERROR: Failed to change nickname or send announcement: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail the settings update if nickname change fails

    return JSONResponse({
        "ok": True,
        "message": "Settings updated successfully",
        "guild_id": guild_id
    })


@app.delete("/api/guilds/{guild_id}/settings")
async def api_delete_guild_settings(guild_id: str, request: Request):
    """Delete bot settings for a specific guild."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify user has access to this guild
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    user_guilds = await auth_service.get_user_guilds(access_token)
    user_guild_ids = {g["id"] for g in user_guilds}
    
    if guild_id not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    # Delete settings from database
    success = await settings_service.delete_settings(guild_id)
    
    if success:
        return JSONResponse({
            "ok": True,
            "message": "Settings deleted successfully",
            "guild_id": guild_id
        })
    else:
        raise HTTPException(status_code=500, detail="Failed to delete settings")
