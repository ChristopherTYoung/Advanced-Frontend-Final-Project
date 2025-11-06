"""Discord Bot Service - Manages Discord bot connection and operations."""

import os
import discord
from discord.ext import commands
import asyncio
from typing import Optional, List, Dict


class BotService:
    """Service for managing Discord bot operations."""

    def __init__(self):
        self.bot_token = os.environ.get("DISCORD_BOT_TOKEN") or os.environ.get("VITE_DISCORD_BOT_TOKEN")
        self.message_service = None  # Will be set by main.py

        # Discord Bot Setup
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.dm_messages = True  # Enable DM intents
        intents.message_content = True  # Required to read message content

        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.bot_task: Optional[asyncio.Task] = None

        # Register event handlers
        self._register_events()

    def _register_events(self):
        """Register Discord bot event handlers."""

        @self.bot.event
        async def on_ready():
            print(f"Bot logged in as {self.bot.user}")
            print(f"Bot is in {len(self.bot.guilds)} guilds:")
            for guild in self.bot.guilds:
                print(f"  - {guild.name} (ID: {guild.id})")

        @self.bot.event
        async def on_error(event, *args, **kwargs):
            print(f"ERROR in event {event}:", args, kwargs)
            import traceback

            traceback.print_exc()

        @self.bot.event
        async def on_message(message: discord.Message):
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return

            print(f"DEBUG: Message received from {message.author.name} in {type(message.channel).__name__}")

            # Handle direct messages
            if isinstance(message.channel, discord.DMChannel):
                print(f"DEBUG: DM detected! Message service connected: {self.message_service is not None}")
                if self.message_service:
                    self.message_service.add_to_history(
                        message_type="dm",
                        content=message.content,
                        user_id=str(message.author.id),
                        username=message.author.name,
                        message_id=str(message.id),
                    )
                    print(f"DEBUG: DM added to history from {message.author.name}: {message.content}")
                else:
                    print("WARNING: Message service not connected!")
                print(f"DM received from {message.author.name}: {message.content}")

            # Handle server/guild messages
            elif isinstance(message.channel, discord.TextChannel):
                print(f"DEBUG: Server message detected! Message service connected: {self.message_service is not None}")
                if self.message_service:
                    guild = message.guild
                    self.message_service.add_to_history(
                        message_type="received",
                        content=message.content,
                        user_id=str(message.author.id),
                        username=message.author.name,
                        guild_id=str(guild.id) if guild else None,
                        guild_name=guild.name if guild else None,
                        channel_id=str(message.channel.id),
                        channel_name=message.channel.name,
                        message_id=str(message.id),
                    )
                    print(
                        f"DEBUG: Server message added to history from {message.author.name} in #{message.channel.name}: {message.content}"
                    )
                else:
                    print("WARNING: Message service not connected!")

            # Allow other command processing
            await self.bot.process_commands(message)

    async def start(self):
        """Start the Discord bot."""
        print(f"DEBUG: DISCORD_BOT_TOKEN configured: {bool(self.bot_token)}")
        if self.bot_token:
            print(f"DEBUG: Token preview: {self.bot_token[:20]}...")
            print(f"DEBUG: Starting Discord bot...")
            try:
                self.bot_task = asyncio.create_task(self.bot.start(self.bot_token))
                print(f"DEBUG: Bot task created successfully")

                # Add a callback to check for errors
                def task_done_callback(task):
                    if task.exception():
                        print(f"ERROR: Bot task failed with exception: {task.exception()}")
                        import traceback

                        traceback.print_exception(
                            type(task.exception()), task.exception(), task.exception().__traceback__
                        )

                self.bot_task.add_done_callback(task_done_callback)
            except Exception as e:
                print(f"ERROR starting bot: {e}")
                import traceback

                traceback.print_exc()
        else:
            print("Warning: DISCORD_BOT_TOKEN not set, bot will not start")

    async def stop(self):
        """Stop the Discord bot."""
        if self.bot_task and not self.bot_task.done():
            await self.bot.close()
            self.bot_task.cancel()

    def is_ready(self) -> bool:
        """Check if bot is ready."""
        return self.bot.is_ready()

    def get_guilds(self) -> List[Dict[str, str]]:
        """Get list of guilds the bot is in."""
        if not self.is_ready():
            return []

        return [
            {"id": str(guild.id), "name": guild.name, "icon": guild.icon.url if guild.icon else None}
            for guild in self.bot.guilds
        ]

    def get_guild_by_id(self, guild_id: int):
        """Get a guild by ID."""
        return self.bot.get_guild(guild_id)

    def get_channel_by_id(self, channel_id: int):
        """Get a channel by ID."""
        return self.bot.get_channel(channel_id)

    async def send_message(self, channel_id: int, message: str, user_id: str = None, username: str = None) -> bool:
        """Send a message to a Discord channel.

        Args:
            channel_id: The channel ID to send to
            message: The message content
            user_id: User ID who sent the message (for history tracking)
            username: Username who sent the message (for history tracking)

        Returns:
            True if successful

        Raises:
            ValueError: If channel not found or invalid type
            discord.Forbidden: If bot lacks permissions
            discord.HTTPException: If Discord API error occurs
        """
        channel = self.get_channel_by_id(channel_id)
        if not channel:
            raise ValueError("Channel not found")

        if not isinstance(channel, discord.TextChannel):
            raise ValueError("Channel is not a text channel")

        sent_message = await channel.send(message)

        # Track in message history
        if self.message_service:
            guild = channel.guild
            self.message_service.add_to_history(
                message_type="sent",
                content=message,
                user_id=user_id,
                username=username,
                guild_id=str(guild.id) if guild else None,
                guild_name=guild.name if guild else None,
                channel_id=str(channel.id),
                channel_name=channel.name,
                message_id=str(sent_message.id),
            )

        return True


# Singleton instance
bot_service = BotService()
