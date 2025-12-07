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
from services.proposal_service import proposal_service
from services.offense_service import OffenseService
from services.llm_tools import tool_send_message
from controllers.auth_controller import router as auth_router
from controllers.guild_controller import router as guild_router
from controllers.message_controller import router as message_router
from controllers.event_controller import router as event_router
from controllers.proposal_controller import router as proposal_router
from controllers.guild_settings_controller import router as guild_settings_router
from controllers.offense_controller import router as offense_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(guild_router)
app.include_router(message_router)
app.include_router(event_router)
app.include_router(proposal_router)
app.include_router(guild_settings_router)
app.include_router(offense_router)

SESSION_SECRET = os.environ.get("DISCORD_SESSION_SECRET", "dev-secret-change-me")
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173")
DISCORD_SESSION_SAMESITE = os.environ.get("DISCORD_SESSION_SAMESITE", "lax")
DISCORD_SESSION_HTTPS_ONLY = os.environ.get("DISCORD_SESSION_HTTPS_ONLY", "false").lower() in ("1", "true", "yes")
DATABASE_URL = os.environ.get("DB_CONNECTION_STRING")

bot_service.message_service = message_service
bot_service.settings_service = settings_service

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
    max_age=86400,  # 24 hours
    domain=None,  # Let browser handle domain automatically
)


@app.on_event("startup")
async def startup_event():
    print(f"DEBUG: Initializing database pool...")
    await message_service.init_db_pool(DATABASE_URL)
    await settings_service.init_db_pool(DATABASE_URL)
    await event_service.init_db_pool(DATABASE_URL)
    await proposal_service.init_db_pool(DATABASE_URL)

    # Set up service dependencies
    proposal_service.event_service = event_service

    offense_service = OffenseService(message_service.db_pool)
    bot_service.offense_service = offense_service

    await bot_service.start()

    async def _event_checker_loop():
        print("DEBUG: Event checker background task started")
        while True:
            now = datetime.utcnow()
            due_events = await event_service.get_due_events(now)
            if due_events:
                print(f"DEBUG: Found {len(due_events)} due event(s)")

            for ev in due_events:
                guild_obj = bot_service.get_guild_by_id(int(ev["guild_id"]))
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
                        personality = await bot_service._get_personality(ev["guild_id"])
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
                        await tool_send_message(bot_service, ev["guild_id"], target_channel_id, resp)
                    else:
                        deleted = await event_service.delete_event(ev["event_id"])

            await asyncio.sleep(60)

    app.state.event_checker_task = asyncio.create_task(_event_checker_loop())


@app.on_event("shutdown")
async def shutdown_event():
    await bot_service.stop()
    await message_service.close_db_pool()
    await settings_service.close_db_pool()
    await event_service.close_db_pool()
    await proposal_service.close_db_pool()
    if bot_service.offense_service:
        await bot_service.offense_service.close()
    task = getattr(app.state, "event_checker_task", None)
    if task and not task.done():
        task.cancel()
