import os
import asyncio
from typing import Optional
from datetime import datetime, timezone

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
from services.event_service import event_service
from services.llm_tools import tool_send_message
from schemas import (
    SendMessageRequest
)

app = FastAPI()

SESSION_SECRET = os.environ.get("DISCORD_SESSION_SECRET", "dev-secret-change-me")
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173")
DISCORD_SESSION_SAMESITE = os.environ.get("DISCORD_SESSION_SAMESITE", "lax")
DISCORD_SESSION_HTTPS_ONLY = os.environ.get("DISCORD_SESSION_HTTPS_ONLY", "false").lower() in ("1", "true", "yes")
DATABASE_URL = os.environ.get("DB_CONNECTION_STRING")

bot_service.message_service = message_service
bot_service.settings_service = settings_service
print(f"DEBUG: Services connected")


@app.on_event("startup")
async def startup_event():
    print(f"DEBUG: Initializing database pool...")
    await message_service.init_db_pool(DATABASE_URL)
    await settings_service.init_db_pool(DATABASE_URL)
    await event_service.init_db_pool(DATABASE_URL)
    print(f"DEBUG: Bot service has message_service: {bot_service.message_service is not None}")
    await bot_service.start()
    # Start background event checker
    async def _event_checker_loop():
        print("DEBUG: Event checker background task started")
        while True:
            try:
                # Use UTC naive datetimes (DB stores TIMESTAMP without tz)
                now = datetime.utcnow()
                due_events = await event_service.get_due_events(now)
                if due_events:
                    print(f"DEBUG: Found {len(due_events)} due event(s)")

                for ev in due_events:
                    try:
                        guild_obj = bot_service.get_guild_by_id(int(ev['guild_id']))
                        if not guild_obj:
                            print(f"WARNING: Guild {ev['guild_id']} not found by bot")
                            continue

                        target_channel_id = None
                        for channel in guild_obj.text_channels:
                            if channel.permissions_for(guild_obj.me).send_messages:
                                target_channel_id = str(channel.id)
                                break

                        if not target_channel_id:
                            print(f"WARNING: No suitable channel to send notification in guild {ev['guild_id']}")
                            continue

                        try:
                            personality = await bot_service._get_personality(ev['guild_id'])
                        except Exception:
                            personality = None

                        system_prompt = llm_service.build_system_prompt(personality=personality, use_tools=True)

                        user_prompt = (
                            f"Create an @everyone announcement for the event '{ev['event_name']}' happening now. "
                            f"Event time: {ev['time_of_event']}. Details: {ev['event_details']}. "
                            f"Target guild_id: '{ev['guild_id']}', channel_id: '{target_channel_id}'."
                        )

                        resp = await llm_service.generate_response(
                            user_message=user_prompt,
                            system_prompt=system_prompt,
                            use_tools=True,
                        )

                        if resp:
                            try:
                                await tool_send_message(bot_service, ev['guild_id'], target_channel_id, resp)
                                print(f"DEBUG: Sent free-form LLM announcement for event {ev['event_id']}")
                            except Exception as e:
                                print(f"ERROR sending free-form LLM announcement for event {ev['event_id']}: {e}")
                                import traceback; traceback.print_exc()
                        else:
                            print(f"DEBUG: LLM executed tool calls or returned no plain text for event {ev['event_id']}")
                    except Exception as e:
                        print(f"ERROR preparing/sending announcement for event {ev.get('event_id')}: {e}")
                        import traceback; traceback.print_exc()
                    finally:
                        try:
                            deleted = await event_service.delete_event(ev['event_id'])
                            if deleted:
                                print(f"DEBUG: Deleted event {ev['event_id']} after processing")
                        except Exception as e:
                            print(f"ERROR deleting event {ev.get('event_id')}: {e}")

            except Exception as e:
                print(f"ERROR in event checker loop: {e}")
                import traceback; traceback.print_exc()

            # Wait 60 seconds between checks
            await asyncio.sleep(60)

    # Schedule the background checker task
    app.state.event_checker_task = asyncio.create_task(_event_checker_loop())


@app.on_event("shutdown")
async def shutdown_event():
    await bot_service.stop()
    await message_service.close_db_pool()
    await settings_service.close_db_pool()
    await event_service.close_db_pool()
    # Cancel background event checker if running
    task = getattr(app.state, 'event_checker_task', None)
    if task and not task.done():
        task.cancel()


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

# Include event routes from controller
from event_controller import router as event_router
app.include_router(event_router)
# Include guild settings routes
from guild_settings_controller import router as guild_settings_router
app.include_router(guild_settings_router)

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"hello": "world"}

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
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not bot_service.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready")

    guild = bot_service.get_guild_by_id(int(guild_id))
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found or bot is not in this guild")

    text_channels = [{"id": str(channel.id), "name": channel.name} for channel in guild.text_channels]

    return JSONResponse({"channels": text_channels})

@app.post("/api/send-message")
async def api_send_message(payload: SendMessageRequest, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not bot_service.is_ready():
        raise HTTPException(status_code=503, detail="Bot is not ready")

    try:
        result = await _send_message_internal(
            guild_id=payload.guild_id,
            channel_id=payload.channel_id,
            message=payload.message,
            instructions=payload.instructions,
            event_details=payload.event_details,
            user=user,
        )
        if result:
            return JSONResponse({"ok": True, "message": "Message sent successfully"})
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except discord.Forbidden:
        raise HTTPException(status_code=403, detail="Bot does not have permission to send messages in this channel")
    except discord.HTTPException as e:
        raise HTTPException(status_code=500, detail=f"Discord API error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


async def _send_message_internal(guild_id: str, channel_id: str, message: Optional[str] = None, instructions: Optional[str] = None, event_details: Optional[str] = None, user: Optional[dict] = None) -> bool:
    if not bot_service.is_ready():
        raise ValueError("Bot is not ready")

    # If instructions provided, generate content using LLM
    final_message = message
    if not final_message and not instructions:
        raise ValueError("Either message or instructions must be provided")

    if instructions:
        prompt = instructions
        if event_details:
            prompt = f"{instructions}\n\nEvent details: {event_details}"

        announcement = await llm_service.generate_response(
            user_message=prompt,
            system_prompt=llm_service.build_system_prompt(use_tools=False),
            use_tools=False,
        )

        final_message = announcement or final_message

    if not final_message:
        raise ValueError("No message content to send")

    # Send via bot_service
    return await bot_service.send_message(int(channel_id), final_message, user_id=(user.get("id") if user else None), username=(user.get("username") if user else None))


@app.post("/api/guilds/{guild_id}/channels/{channel_id}/messages")
async def api_send_message_to_channel(guild_id: str, channel_id: str, payload: SendMessageRequest, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        ok = await _send_message_internal(
            guild_id=guild_id,
            channel_id=channel_id,
            message=payload.message,
            instructions=payload.instructions,
            event_details=payload.event_details,
            user=user,
        )
        if ok:
            return JSONResponse({"ok": True, "message": "Message sent successfully"})
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/messages")
async def api_get_messages(request: Request, limit: int = 50, message_type: str = None):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    limit = min(limit, 100)

    messages = await message_service.get_history(limit=limit, message_type=message_type)

    return JSONResponse({"messages": messages})


@app.get("/api/messages/dm")
async def api_get_dm_messages(request: Request, limit: int = 50):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    limit = min(limit, 100)

    messages = await message_service.get_dm_messages(limit=limit)
    print(f"DEBUG: Returning {len(messages)} DM messages")

    return JSONResponse({"messages": messages})