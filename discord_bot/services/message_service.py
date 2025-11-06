"""Message Service - Manages Discord bot messages and history."""

from typing import List, Dict, Any
from datetime import datetime
import discord
from discord.ext import commands


class MessageService:
    """Service for managing bot messages and message history."""

    def __init__(self):
        self.message_history: List[Dict[str, Any]] = []
        self.max_history = 100  # Keep last 100 messages

    def add_to_history(
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
        message_entry = {
            "id": message_id or str(datetime.utcnow().timestamp()),
            "type": message_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "username": username,
            "guild_id": guild_id,
            "guild_name": guild_name,
            "channel_id": channel_id,
            "channel_name": channel_name,
        }

        self.message_history.append(message_entry)
        print(f"DEBUG MessageService: Added {message_type} message. Total history: {len(self.message_history)}")

        # Keep only the most recent messages
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history :]

    def get_history(self, limit: int = 50, message_type: str = None, user_id: str = None) -> List[Dict[str, Any]]:
        messages = self.message_history

        # Apply filters
        if message_type:
            messages = [m for m in messages if m["type"] == message_type]

        if user_id:
            messages = [m for m in messages if m["user_id"] == user_id]

        # Return most recent first, limited
        return list(reversed(messages[-limit:]))

    def get_dm_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.get_history(limit=limit, message_type="dm")

    def clear_history(self):
        """Clear all message history."""
        self.message_history = []

    def register_bot_handlers(self, bot: commands.Bot):
        @bot.event
        async def on_message(message: discord.Message):
            # Ignore messages from the bot itself
            if message.author == bot.user:
                return

            # Handle direct messages
            if isinstance(message.channel, discord.DMChannel):
                self.add_to_history(
                    message_type="dm",
                    content=message.content,
                    user_id=str(message.author.id),
                    username=message.author.name,
                    message_id=str(message.id),
                )
                print(f"DM received from {message.author.name}: {message.content}")

            # Allow other command processing
            await bot.process_commands(message)


# Singleton instance
message_service = MessageService()
