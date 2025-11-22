from typing import Optional, Dict, Any
from datetime import datetime
import asyncpg
import json


class SettingsService:
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None

    async def init_db_pool(self, database_url: str):
        self.db_pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)
        print("DEBUG SettingsService: Database pool initialized")

    async def close_db_pool(self):
        """Close database connection pool."""
        if self.db_pool:
            await self.db_pool.close()
            print("DEBUG SettingsService: Database pool closed")

    async def get_settings(self, guild_id: str) -> Optional[Dict[str, Any]]:
        if not self.db_pool:
            print("WARNING SettingsService: Database pool not initialized")
            return None
        
        async with self.db_pool.acquire() as conn:
            # Prefer the new columns (bot_settings, role_settings). If the DB still
            # contains the old `settings` column, fall back to that for compatibility.
            row = await conn.fetchrow(
                "SELECT bot_settings, role_settings, content_maturity_preferences, edited_at FROM guild_bot_settings WHERE guild_id = $1",
                guild_id
            )

            if row:
                try:
                    bot_settings_data = row["bot_settings"]
                    role_settings_data = row["role_settings"]
                except Exception:
                    old_row = await conn.fetchrow(
                        "SELECT settings, edited_at FROM guild_bot_settings WHERE guild_id = $1",
                        guild_id
                    )
                    if not old_row:
                        return None
                    settings_data = old_row["settings"]
                    if isinstance(settings_data, str):
                        settings_data = json.loads(settings_data)
                    return {
                        "guild_id": guild_id,
                        "settings": settings_data,
                        "edited_at": old_row["edited_at"].isoformat() if old_row["edited_at"] else None
                    }

                if isinstance(bot_settings_data, str):
                    try:
                        bot_settings_data = json.loads(bot_settings_data)
                    except Exception:
                        bot_settings_data = None

                if isinstance(role_settings_data, str):
                    try:
                        role_settings_data = json.loads(role_settings_data)
                    except Exception:
                        role_settings_data = None

                content_maturity_data = row["content_maturity_preferences"]
                if isinstance(content_maturity_data, str):
                    try:
                        content_maturity_data = json.loads(content_maturity_data)
                    except Exception:
                        content_maturity_data = None

                settings_container = {
                    "bot_settings": bot_settings_data if bot_settings_data is not None else {},
                    "role_settings": role_settings_data if role_settings_data is not None else {"roles": []},
                    "content_maturity_preferences": content_maturity_data if content_maturity_data is not None else {}
                }

                return {
                    "guild_id": guild_id,
                    "settings": settings_container,
                    "edited_at": row["edited_at"].isoformat() if row["edited_at"] else None
                }

            return None

    async def update_settings(self, guild_id: str, settings: Dict[str, Any]) -> bool:
        if not self.db_pool:
            print("WARNING SettingsService: Database pool not initialized")
            return False

        async with self.db_pool.acquire() as conn:
            bot_settings = settings.get("bot_settings") if isinstance(settings, dict) else None
            role_settings = settings.get("role_settings") if isinstance(settings, dict) else None
            content_maturity = settings.get("content_maturity_preferences") if isinstance(settings, dict) else None

            if bot_settings is None and isinstance(settings, dict):
                if "personality" in settings or "bot_nickname" in settings:
                    bot_settings = {k: settings.get(k) for k in ("personality", "bot_nickname") if k in settings}

            if role_settings is not None and isinstance(role_settings, list):
                role_settings = {"roles": role_settings}

            await conn.execute(
                """
                INSERT INTO guild_bot_settings (guild_id, bot_settings, role_settings, content_maturity_preferences, edited_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (guild_id) 
                DO UPDATE SET 
                    bot_settings = EXCLUDED.bot_settings,
                    role_settings = EXCLUDED.role_settings,
                    content_maturity_preferences = EXCLUDED.content_maturity_preferences,
                    edited_at = EXCLUDED.edited_at
                """,
                guild_id,
                json.dumps(bot_settings) if bot_settings is not None else None,
                json.dumps(role_settings) if role_settings is not None else None,
                json.dumps(content_maturity) if content_maturity is not None else None,
                datetime.utcnow()
            )
            print(f"DEBUG SettingsService: Updated settings for guild {guild_id}")
            return True

    async def delete_settings(self, guild_id: str) -> bool:
        if not self.db_pool:
            print("WARNING SettingsService: Database pool not initialized")
            return False

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM guild_bot_settings WHERE guild_id = $1",
                guild_id
            )
            print(f"DEBUG SettingsService: Deleted settings for guild {guild_id}")
            return True

settings_service = SettingsService()