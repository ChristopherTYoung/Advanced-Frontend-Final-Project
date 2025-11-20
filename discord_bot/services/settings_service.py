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
            row = await conn.fetchrow(
                "SELECT settings, edited_at FROM guild_bot_settings WHERE guild_id = $1",
                guild_id
            )
            
            if row:
                settings_data = row["settings"]
                if isinstance(settings_data, str):
                    settings_data = json.loads(settings_data)
                
                return {
                    "guild_id": guild_id,
                    "settings": settings_data,
                    "edited_at": row["edited_at"].isoformat() if row["edited_at"] else None
                }
            return None

    async def update_settings(self, guild_id: str, settings: Dict[str, Any]) -> bool:
        if not self.db_pool:
            print("WARNING SettingsService: Database pool not initialized")
            return False

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO guild_bot_settings (guild_id, settings, edited_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id) 
                DO UPDATE SET 
                    settings = EXCLUDED.settings,
                    edited_at = EXCLUDED.edited_at
                """,
                guild_id,
                json.dumps(settings),
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