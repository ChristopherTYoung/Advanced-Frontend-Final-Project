"""Message Service - Manages Discord bot messages and history."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import discord
from discord.ext import commands
import asyncpg


class MessageService:
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None

    async def init_db_pool(self, database_url: str):
        self.db_pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)
        print("DEBUG MessageService: Database pool initialized")

    async def close_db_pool(self):
        """Close database connection pool."""
        if self.db_pool:
            await self.db_pool.close()
            print("DEBUG MessageService: Database pool closed")

    async def add_to_history(
        self,
        message_type: str,
        content: str,
        user_id: str = None,
        username: str = None,
        guild_id: str = None,
        guild_name: str = None,
        channel_id: str = None,
        channel_name: str = None,
        message_id: str = None,
    ):
        if not self.db_pool:
            print("WARNING MessageService: Database pool not initialized, skipping message storage")
            return

        role_mapping = {"dm": "user", "received": "user", "sent": "assistant"}
        role = role_mapping.get(message_type, "user")

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO message (guild_id, channel_id, user_id, role, body, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                guild_id or "DM",
                channel_id or "DM",
                user_id or "Unknown",
                role,
                content,
                datetime.utcnow(),
            )

    async def get_history(
        self,
        limit: int = 50,
        message_type: str = None,
        user_id: str = None,
        guild_id: str = None,
        channel_id: str = None,
    ) -> List[Dict[str, Any]]:
        if not self.db_pool:
            print("WARNING MessageService: Database pool not initialized")
            return []

        async with self.db_pool.acquire() as conn:
            query = "SELECT message_id, guild_id, channel_id, user_id, role, body, created_at FROM message WHERE 1=1"
            params = []
            param_count = 1

            if guild_id:
                query += f" AND guild_id = ${param_count}"
                params.append(guild_id)
                param_count += 1

            if channel_id:
                query += f" AND channel_id = ${param_count}"
                params.append(channel_id)
                param_count += 1

            if user_id:
                query += f" AND user_id = ${param_count}"
                params.append(user_id)
                param_count += 1

            if message_type:
                role_mapping = {"dm": "user", "received": "user", "sent": "assistant"}
                role = role_mapping.get(message_type, "user")
                query += f" AND role = ${param_count}"
                params.append(role)
                param_count += 1

            query += f" ORDER BY created_at DESC LIMIT ${param_count}"
            params.append(limit)

            rows = await conn.fetch(query, *params)

            messages = []
            for row in reversed(rows):
                messages.append(
                    {
                        "id": str(row["message_id"]),
                        "type": "sent" if row["role"] == "assistant" else "received",
                        "content": row["body"],
                        "timestamp": row["created_at"].isoformat(),
                        "user_id": row["user_id"] if row["user_id"] != "Unknown" else None,
                        "username": None,
                        "guild_id": row["guild_id"] if row["guild_id"] != "DM" else None,
                        "guild_name": None,
                        "channel_id": row["channel_id"] if row["channel_id"] != "DM" else None,
                        "channel_name": None,
                    }
                )
            return messages

    async def get_dm_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.get_history(limit=limit, guild_id="DM")


message_service = MessageService()
