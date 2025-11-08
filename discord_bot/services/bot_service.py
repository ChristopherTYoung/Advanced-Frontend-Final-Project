import os
import discord
from discord.ext import commands
import asyncio
from typing import Optional, List, Dict, Any
from services.llm_service import llm_service


class BotService:
    """Service for managing Discord bot operations."""

    def __init__(self):
        self.bot_token = os.environ.get("DISCORD_BOT_TOKEN") or os.environ.get("VITE_DISCORD_BOT_TOKEN")
        self.message_service = None  # Will be set by main.py
        self.settings_service = None  # Will be set by main.py

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

        # Register LLM tools
        self._register_llm_tools()

    def _register_llm_tools(self):
        """Register tools that the LLM can call."""

        # Tool: Get list of guilds (servers)
        llm_service.register_tool(
            name="get_guilds",
            description="Get a list of Discord servers (guilds) that the bot is in",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            function=self._tool_get_guilds,
        )

        # Tool: Get channels in a guild
        llm_service.register_tool(
            name="get_channels",
            description="Get a list of text channels in a specific Discord server (guild)",
            parameters={
                "type": "object",
                "properties": {
                    "guild_id": {
                        "type": "string",
                        "description": "The ID of the guild/server to get channels from",
                    }
                },
                "required": ["guild_id"],
            },
            function=self._tool_get_channels,
        )

        # Tool: Get message history
        llm_service.register_tool(
            name="get_message_history",
            description="Get recent message history from the bot",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of messages to return (default 10, max 50)",
                        "default": 10,
                    },
                    "message_type": {
                        "type": "string",
                        "description": "Filter by message type: 'dm', 'received', or 'sent'",
                        "enum": ["dm", "received", "sent"],
                    },
                },
                "required": [],
            },
            function=self._tool_get_message_history,
        )

        llm_service.register_tool(
            name="change_bot_nickname",
            description="Change the bot's nickname in a specific Discord server (guild)",
            parameters={
                "type": "object",
                "properties": {
                    "guild_id": {
                        "type": "string",
                        "description": "The ID of the guild/server where the nickname should be changed",
                    },
                    "nickname": {
                        "type": "string",
                        "description": "The new nickname for the bot (max 32 characters). Use null or empty string to reset to default username.",
                    },
                },
                "required": ["guild_id"],
            },
            function=self._tool_change_bot_nickname,
        )

    async def _tool_get_guilds(self) -> Dict[str, Any]:
        """Tool function: Get list of guilds."""
        try:
            guilds = self.get_guilds()
            return {"success": True, "guilds": guilds, "count": len(guilds)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_get_channels(self, guild_id: str) -> Dict[str, Any]:
        """Tool function: Get channels in a guild."""
        try:
            guild = self.get_guild_by_id(int(guild_id))
            if not guild:
                return {"success": False, "error": "Guild not found"}

            channels = [
                {"id": str(channel.id), "name": channel.name, "type": "text"}
                for channel in guild.text_channels
            ]
            return {"success": True, "guild_name": guild.name, "channels": channels, "count": len(channels)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_get_message_history(
        self, limit: int = 10, message_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tool function: Get message history."""
        try:
            if not self.message_service:
                return {"success": False, "error": "Message service not available"}

            limit = min(limit, 50)  # Cap at 50
            messages = await self.message_service.get_history(limit=limit, message_type=message_type)
            return {"success": True, "messages": messages, "count": len(messages)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_change_bot_nickname(self, guild_id: str, nickname: Optional[str] = None) -> Dict[str, Any]:
        """Tool function: Change bot nickname in a guild."""
        try:
            guild = self.get_guild_by_id(int(guild_id))
            if not guild:
                return {"success": False, "error": f"Guild with ID {guild_id} not found"}

            # Get the bot's member object in the guild
            bot_member = guild.get_member(self.bot.user.id)
            if not bot_member:
                return {"success": False, "error": "Bot is not a member of this guild"}

            # Check if bot has permission to change its own nickname
            if not guild.me.guild_permissions.change_nickname:
                return {
                    "success": False, 
                    "error": "Bot does not have permission to change its nickname in this guild"
                }

            # Change the nickname (empty string or None resets to default)
            old_nickname = bot_member.nick or self.bot.user.name
            await bot_member.edit(nick=nickname if nickname else None)
            new_nickname = nickname if nickname else self.bot.user.name

            return {
                "success": True,
                "message": f"Bot nickname changed in {guild.name}",
                "old_nickname": old_nickname,
                "new_nickname": new_nickname,
                "guild_name": guild.name,
                "guild_id": guild_id
            }
        except discord.Forbidden:
            return {"success": False, "error": "Bot lacks permissions to change nickname"}
        except discord.HTTPException as e:
            return {"success": False, "error": f"Discord API error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _register_events(self):
        """Register Discord bot event handlers."""

        @self.bot.event
        async def on_ready():
            print(f"Bot logged in as {self.bot.user}")
            print(f"Bot is in {len(self.bot.guilds)} guilds:")
            for guild in self.bot.guilds:
                print(f"  - {guild.name} (ID: {guild.id})")

        @self.bot.event
        async def on_guild_join(guild: discord.Guild):
            """Called when the bot joins a new guild."""
            print(f"Bot joined guild: {guild.name} (ID: {guild.id})")

        @self.bot.event
        async def on_guild_remove(guild: discord.Guild):
            """Called when the bot is removed from a guild."""
            print(f"Bot removed from guild: {guild.name} (ID: {guild.id})")

        @self.bot.event
        async def on_error(event, *args, **kwargs):
            print(f"ERROR in event {event}:", args, kwargs)
            import traceback

            traceback.print_exc()

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author == self.bot.user:
                return

            print(f"DEBUG: Message received from {message.author.name} in {type(message.channel).__name__}")

            if isinstance(message.channel, discord.DMChannel):
                await self._handle_dm(message)
                
            elif isinstance(message.channel, discord.TextChannel):
                await self._handle_server_message(message)

            await self.bot.process_commands(message)

    async def _build_conversation_history(
        self, user_id: str = None, guild_id: str = None, channel_id: str = None, limit: int = 10
    ) -> List[Dict[str, str]]:
        if not self.message_service:
            return []

        try:
            if user_id and not guild_id:
                messages = await self.message_service.get_history(
                    limit=limit * 2, 
                    guild_id="DM",
                    channel_id=channel_id
                )
            elif guild_id and channel_id:
                # Server messages - filter by guild and channel
                messages = await self.message_service.get_history(
                    limit=limit * 2,
                    guild_id=guild_id,
                    channel_id=channel_id
                )
            else:
                messages = await self.message_service.get_history(limit=limit * 2)

            # Convert to LLM format (limit to most recent)
            conversation = []
            for msg in messages[-limit:]:
                msg_type = msg.get("type")
                content = msg.get("content", "")
                username = msg.get("username", "Unknown")

                # Map message types to LLM roles
                if msg_type == "sent":
                    # Bot's messages
                    conversation.append({"role": "assistant", "content": content})
                elif msg_type in ["dm", "received"]:
                    # User's messages
                    conversation.append({"role": "user", "content": f"{username}: {content}"})

            return conversation
        except Exception as e:
            print(f"ERROR building conversation history: {e}")
            import traceback
            traceback.print_exc()
            return []
            

    async def _get_personality(self, guild_id: Optional[str]) -> Optional[str]:
        if not guild_id or guild_id == "DM" or not self.settings_service:
            return None
            
        try:
            settings = await self.settings_service.get_settings(guild_id)
            if settings and settings.get("settings"):
                return settings["settings"].get("personality")
        except Exception as e:
            print(f"ERROR fetching personality settings: {e}")
            return None
        
        return None

    async def _handle_dm(self, message: discord.Message):
        print(f"DEBUG: DM detected! Message service connected: {self.message_service is not None}")
        
        if self.message_service:
            await self.message_service.add_to_history(
                message_type="dm",
                content=message.content,
                user_id=str(message.author.id),
                username=message.author.name,
                guild_id="DM",
                channel_id=str(message.channel.id),
                message_id=str(message.id),
            )
            print(f"DEBUG: DM added to history from {message.author.name}: {message.content}")
        else:
            print("WARNING: Message service not connected!")
        
        print(f"DM received from {message.author.name}: {message.content}")

        # Build conversation history for context (pass channel_id for DM filtering)
        conversation_history = await self._build_conversation_history(
            user_id=str(message.author.id), 
            channel_id=str(message.channel.id),
            limit=10
        )
        print(f"DEBUG: Built conversation history with {len(conversation_history)} messages for DM")

        print(f"DEBUG: Generating LLM response for DM from {message.author.name}")
        
        # DMs don't have guild-specific personality
        llm_response = await llm_service.generate_discord_response(
            user_message=message.content, 
            username=message.author.name, 
            is_dm=True,
            conversation_history=conversation_history,
            personality=None  # No personality for DMs
        )

        if llm_response:
            print(f"DEBUG: LLM response generated: {llm_response[:100]}...")
            await message.channel.send(llm_response)
            print(f"DEBUG: LLM response sent to {message.author.name}")

            if self.message_service:
                await self.message_service.add_to_history(
                    message_type="sent",
                    content=llm_response,
                    user_id=str(self.bot.user.id),
                    username=self.bot.user.name,
                    guild_id="DM",
                    channel_id=str(message.channel.id),
                )
        else:
            print("ERROR: Failed to generate LLM response")
            await message.channel.send("Sorry, I'm having trouble generating a response right now.")

    async def _handle_server_message(self, message: discord.Message):
        print(f"DEBUG: Server message detected! Message service connected: {self.message_service is not None}")
        
        if self.message_service:
            guild = message.guild
            await self.message_service.add_to_history(
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

        # Build conversation history for context
        guild = message.guild
        conversation_history = await self._build_conversation_history(
            guild_id=str(guild.id) if guild else None,
            channel_id=str(message.channel.id),
            limit=10
        )
        print(f"DEBUG: Built conversation history with {len(conversation_history)} messages for server")

        # Get personality settings for this guild
        guild_id_str = str(guild.id) if guild else None
        personality = await self._get_personality(guild_id_str)
        if personality:
            print(f"DEBUG: Using personality setting for guild {guild_id_str}: {personality[:50]}...")

        print(f"DEBUG: Generating LLM response for server message from {message.author.name}")
        
        llm_response = await llm_service.generate_discord_response(
            user_message=message.content,
            username=message.author.name,
            is_dm=False,
            channel_name=message.channel.name,
            guild_id=guild_id_str,
            guild_name=guild.name if guild else None,
            conversation_history=conversation_history,
            use_tools=True,
            personality=personality
        )

        if llm_response:
            print(f"DEBUG: LLM response generated: {llm_response[:100]}...")
            sent_message = await message.channel.send(llm_response)
            print(f"DEBUG: LLM response sent to #{message.channel.name}")

            # Track bot's response in history
            if self.message_service:
                guild = message.guild
                await self.message_service.add_to_history(
                    message_type="sent",
                    content=llm_response,
                    user_id=str(self.bot.user.id),
                    username=self.bot.user.name,
                    guild_id=str(guild.id) if guild else None,
                    guild_name=guild.name if guild else None,
                    channel_id=str(message.channel.id),
                    channel_name=message.channel.name,
                    message_id=str(sent_message.id),
                )
        else:
            print("ERROR: Failed to generate LLM response")
            await message.channel.send("Sorry, I'm having trouble generating a response right now.")

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
        channel = self.get_channel_by_id(channel_id)
        if not channel:
            raise ValueError("Channel not found")

        if not isinstance(channel, discord.TextChannel):
            raise ValueError("Channel is not a text channel")

        sent_message = await channel.send(message)

        # Track in message history
        if self.message_service:
            guild = channel.guild
            await self.message_service.add_to_history(
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

bot_service = BotService()