"""Message Service - Manages Discord bot messages and history."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import discord
from discord.ext import commands
import asyncpg


class MessageService:
    """Service for managing bot messages and message history with database persistence."""
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None

    async def init_db_pool(self, database_url: str):
        try:
            self.db_pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)
            print("DEBUG MessageService: Database pool initialized")
        except Exception as e:
            print(f"ERROR MessageService: Failed to initialize database pool: {e}")
            import traceback
            traceback.print_exc()

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

        try:
            # Map message_type to role for database
            role_mapping = {"dm": "user", "received": "user", "sent": "assistant"}
            role = role_mapping.get(message_type, "user")

            async with self.db_pool.acquire() as conn:
                # Insert message into database with channel_id and user_id
                await conn.execute(
                    """
                    INSERT INTO message (guild_id, channel_id, user_id, role, body, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    guild_id or "DM",  # Use 'DM' as guild_id for direct messages
                    channel_id or "DM",  # Use 'DM' as channel_id for direct messages
                    user_id or "Unknown",
                    role,
                    content,
                    datetime.utcnow(),
                )
                print(f"DEBUG MessageService: Added {message_type} message to database from user {user_id}")
        except Exception as e:
            print(f"ERROR MessageService: Failed to add message to database: {e}")
            import traceback
            traceback.print_exc()

    async def get_history(
        self, limit: int = 50, message_type: str = None, user_id: str = None, guild_id: str = None, channel_id: str = None
    ) -> List[Dict[str, Any]]:
        if not self.db_pool:
            print("WARNING MessageService: Database pool not initialized")
            return []

        try:
            async with self.db_pool.acquire() as conn:
                # Build query with filters
                query = "SELECT message_id, guild_id, channel_id, user_id, role, body, created_at FROM message WHERE 1=1"
                params = []
                param_count = 1

                # Filter by guild_id
                if guild_id:
                    query += f" AND guild_id = ${param_count}"
                    params.append(guild_id)
                    param_count += 1

                # Filter by channel_id
                if channel_id:
                    query += f" AND channel_id = ${param_count}"
                    params.append(channel_id)
                    param_count += 1

                # Filter by user_id
                if user_id:
                    query += f" AND user_id = ${param_count}"
                    params.append(user_id)
                    param_count += 1

                # Filter by message_type (map to role)
                if message_type:
                    role_mapping = {"dm": "user", "received": "user", "sent": "assistant"}
                    role = role_mapping.get(message_type, "user")
                    query += f" AND role = ${param_count}"
                    params.append(role)
                    param_count += 1

                # Order by most recent and limit
                query += f" ORDER BY created_at DESC LIMIT ${param_count}"
                params.append(limit)

                rows = await conn.fetch(query, *params)

                # Convert to dictionary format
                messages = []
                for row in reversed(rows):  # Reverse to get oldest first
                    messages.append(
                        {
                            "id": str(row["message_id"]),
                            "type": "sent" if row["role"] == "assistant" else "received",
                            "content": row["body"],
                            "timestamp": row["created_at"].isoformat(),
                            "user_id": row["user_id"] if row["user_id"] != "Unknown" else None,
                            "username": None,  # Not stored in current schema
                            "guild_id": row["guild_id"] if row["guild_id"] != "DM" else None,
                            "guild_name": None,  # Not stored in current schema
                            "channel_id": row["channel_id"] if row["channel_id"] != "DM" else None,
                            "channel_name": None,  # Not stored in current schema
                        }
                    )
                return messages
        except Exception as e:
            print(f"ERROR MessageService: Failed to get history from database: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_dm_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get direct messages from database."""
        return await self.get_history(limit=limit, guild_id="DM")
# Singleton instance
message_service = MessageService()