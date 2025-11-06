"""Main FastAPI application."""

import os
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
import discord

from services.bot_service import bot_service
from services.auth_service import auth_service
from services.message_service import message_service


app = FastAPI()

# Configuration
SESSION_SECRET = os.environ.get("DISCORD_SESSION_SECRET", "dev-secret-change-me")
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173")
DISCORD_SESSION_SAMESITE = os.environ.get("DISCORD_SESSION_SAMESITE", "lax")
DISCORD_SESSION_HTTPS_ONLY = os.environ.get("DISCORD_SESSION_HTTPS_ONLY", "false").lower() in ("1", "true", "yes")

# Connect services
bot_service.message_service = message_service
print(f"DEBUG: Message service connected to bot service")


# Lifecycle Events
@app.on_event("startup")
async def startup_event():
    """Start the Discord bot on application startup."""
    print(f"DEBUG: Bot service has message_service: {bot_service.message_service is not None}")
    await bot_service.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the Discord bot on application shutdown."""
    await bot_service.stop()


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in FRONTEND_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site=DISCORD_SESSION_SAMESITE,
    https_only=DISCORD_SESSION_HTTPS_ONLY,
)


# Request Models
class SendMessageRequest(BaseModel):
    guild_id: str
    channel_id: str
    message: str


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
    """Get message history.

    Query params:
        limit: Maximum number of messages to return (default: 50, max: 100)
        message_type: Filter by type ('sent', 'dm', 'received')
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Limit the limit :)
    limit = min(limit, 100)

    messages = message_service.get_history(limit=limit, message_type=message_type)

    return JSONResponse({"messages": messages})


@app.get("/api/messages/dm")
async def api_get_dm_messages(request: Request, limit: int = 50):
    """Get direct messages sent to the bot."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Limit the limit
    limit = min(limit, 100)

    messages = message_service.get_dm_messages(limit=limit)
    print(f"DEBUG: Returning {len(messages)} DM messages")
    print(f"DEBUG: Message service has {len(message_service.message_history)} total messages")

    return JSONResponse({"messages": messages})
