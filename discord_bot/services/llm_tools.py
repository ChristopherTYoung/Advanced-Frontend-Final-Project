from typing import Optional, Dict, Any
import functools
import discord
from datetime import datetime

async def tool_get_guilds(bot_service) -> Dict[str, Any]:
    try:
        guilds = bot_service.get_guilds()
        return {"success": True, "guilds": guilds, "count": len(guilds)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_get_channels(bot_service, guild_id: str) -> Dict[str, Any]:
    try:
        guild = bot_service.get_guild_by_id(int(guild_id))
        if not guild:
            return {"success": False, "error": "Guild not found"}

        channels = [
            {"id": str(channel.id), "name": channel.name, "type": "text"}
            for channel in guild.text_channels
        ]
        return {"success": True, "guild_name": guild.name, "channels": channels, "count": len(channels)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_get_message_history(bot_service, limit: int = 10, message_type: Optional[str] = None) -> Dict[str, Any]:
    try:
        if not getattr(bot_service, "message_service", None):
            return {"success": False, "error": "Message service not available"}

        limit = min(limit, 50)
        messages = await bot_service.message_service.get_history(limit=limit, message_type=message_type)
        return {"success": True, "messages": messages, "count": len(messages)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_change_bot_nickname(bot_service, guild_id: str, nickname: Optional[str] = None) -> Dict[str, Any]:
    try:
        guild = bot_service.get_guild_by_id(int(guild_id))
        if not guild:
            return {"success": False, "error": f"Guild with ID {guild_id} not found"}

        bot_member = guild.get_member(bot_service.bot.user.id)
        if not bot_member:
            return {"success": False, "error": "Bot is not a member of this guild"}

        if not guild.me.guild_permissions.change_nickname:
            return {"success": False, "error": "Bot does not have permission to change its nickname in this guild"}

        old_nickname = bot_member.nick or bot_service.bot.user.name
        await bot_member.edit(nick=nickname if nickname else None)
        new_nickname = nickname if nickname else bot_service.bot.user.name

        return {
            "success": True,
            "message": f"Bot nickname changed in {guild.name}",
            "old_nickname": old_nickname,
            "new_nickname": new_nickname,
            "guild_name": guild.name,
            "guild_id": guild_id,
        }
    except discord.Forbidden:
        return {"success": False, "error": "Bot lacks permissions to change nickname"}
    except discord.HTTPException as e:
        return {"success": False, "error": f"Discord API error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_send_message(bot_service, guild_id: str, channel_id: str, message: str) -> Dict[str, Any]:
    try:
        if not bot_service.is_ready():
            return {"success": False, "error": "Bot is not ready"}

        guild = bot_service.get_guild_by_id(int(guild_id))
        if not guild:
            return {"success": False, "error": "Guild not found"}

        channel = None
        for ch in guild.text_channels:
            if str(ch.id) == str(channel_id):
                channel = ch
                break

        if not channel:
            ch_obj = bot_service.get_channel_by_id(int(channel_id))
            if ch_obj and isinstance(ch_obj, discord.TextChannel):
                channel = ch_obj

        if not channel:
            return {"success": False, "error": "Channel not found or not a text channel"}

        await bot_service.send_message(int(channel.id), message)
        return {"success": True, "message": "Message sent"}
    except discord.Forbidden:
        return {"success": False, "error": "Bot lacks permissions to send message in that channel"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_propose_event(bot_service, guild_id: str, user_id: str, time_of_event: str, event_name: str, event_details: Optional[str] = "") -> Dict[str, Any]:
    try:
        from .event_service import event_service
        try:
            dt = datetime.fromisoformat(time_of_event)
        except Exception:
            return {"success": False, "error": "Invalid time_of_event format; expected ISO datetime"}

        proposal_id = await event_service.create_proposal(
            guild_id=guild_id,
            user_id=user_id,
            time_of_event=dt,
            event_name=event_name,
            event_details=event_details or "",
        )

        if not proposal_id:
            return {"success": False, "error": "Failed to create proposal"}

        return {"success": True, "proposal_id": proposal_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_remove_offensive_message(
    bot_service, 
    guild_id: str, 
    channel_id: str, 
    message_id: str, 
    user_id: str,
    reason: str,
    message_content: str,
    warning_message: str,
    offensive_score: int
) -> Dict[str, Any]:
    """Remove a message that violates server content maturity rules"""
    try:
        print(f"DEBUG: tool_remove_offensive_message called for message {message_id}")
        
        guild = bot_service.get_guild_by_id(int(guild_id))
        if not guild:
            return {"success": False, "error": "Guild not found"}

        channel = bot_service.get_channel_by_id(int(channel_id))
        if not channel or not isinstance(channel, discord.TextChannel):
            return {"success": False, "error": "Channel not found"}

        # Fetch message and download attachments before deleting
        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            print(f"DEBUG: Message {message_id} already deleted")
            return {"success": False, "error": "Message already deleted"}
        except discord.Forbidden:
            return {"success": False, "error": "Bot lacks permission to access message"}

        picture_data = None
        if bot_service.offense_service and message.attachments:
            try:
                for attachment in message.attachments:
                    if attachment.content_type and 'image' in attachment.content_type:
                        import httpx
                        async with httpx.AsyncClient() as client:
                            img_response = await client.get(attachment.url)
                            if img_response.status_code == 200:
                                picture_data = img_response.content
                        break
            except Exception as e:
                print(f"ERROR downloading attachment: {e}")

        # Delete the message
        try:
            await message.delete()
            print(f"DEBUG: Deleted message {message_id}")
        except discord.NotFound:
            print(f"DEBUG: Message {message_id} already deleted")
            return {"success": False, "error": "Message already deleted"}
        except discord.Forbidden:
            return {"success": False, "error": "Bot lacks permission to delete messages"}

        # Record the offense in database
        if bot_service.offense_service:
            await bot_service.offense_service.record_offense(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                body=message_content,
                picture=picture_data,
                offensive_score=offensive_score
            )

        # Send warning message
        await channel.send(warning_message)
        print(f"DEBUG: Sent warning message for offense")

        return {
            "success": True,
            "message": "Offensive message removed and warning sent",
            "reason": reason
        }

    except Exception as e:
        print(f"ERROR in tool_remove_offensive_message: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def register_tools(llm_service, bot_service):
    llm_service.register_tool(
        name="get_guilds",
        description="Get a list of Discord servers (guilds) that the bot is in",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        function=functools.partial(tool_get_guilds, bot_service),
    )

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
        function=functools.partial(tool_get_channels, bot_service),
    )

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
        function=functools.partial(tool_get_message_history, bot_service),
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
        function=functools.partial(tool_change_bot_nickname, bot_service),
    )

    llm_service.register_tool(
        name="propose_event",
        description="Propose an event for admin approval. The proposal will be stored until approved.",
        parameters={
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "Guild ID where the event is proposed"},
                "user_id": {"type": "string", "description": "ID of the user proposing the event"},
                "time_of_event": {"type": "string", "description": "ISO datetime of the proposed event"},
                "event_name": {"type": "string", "description": "Short event title"},
                "event_details": {"type": "string", "description": "Full event details"},
            },
            "required": ["guild_id", "user_id", "time_of_event", "event_name"],
        },
        function=functools.partial(tool_propose_event, bot_service),
    )

    llm_service.register_tool(
        name="send_message",
        description="Send a message to a specific channel in a guild",
        parameters={
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "Guild ID where to send the message"},
                "channel_id": {"type": "string", "description": "Channel ID where to send the message"},
                "message": {"type": "string", "description": "Message content to send"},
            },
            "required": ["guild_id", "channel_id", "message"],
        },
        function=functools.partial(tool_send_message, bot_service),
    )

    llm_service.register_tool(
        name="remove_offensive_message",
        description="Remove a message that violates server content maturity rules and record it as an offense. Use this when content exceeds maturity limits or contains banned content.",
        parameters={
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "Guild ID where the message was sent"},
                "channel_id": {"type": "string", "description": "Channel ID where the message was sent"},
                "message_id": {"type": "string", "description": "ID of the message to remove"},
                "user_id": {"type": "string", "description": "ID of the user who sent the message"},
                "reason": {"type": "string", "description": "Reason for removal (e.g., 'content score 8/10 exceeds limit', 'contains banned content')"},
                "message_content": {"type": "string", "description": "The content of the message being removed"},
                "warning_message": {"type": "string", "description": "Warning message to send to the channel after removal (mention the user and explain the violation)"},
                "offensive_score": {"type": "integer", "description": "Maturity score from 0-10 that you rated this content (0=G-rated, 10=extreme)"},
            },
            "required": ["guild_id", "channel_id", "message_id", "user_id", "reason", "message_content", "warning_message", "offensive_score"],
        },
        function=functools.partial(tool_remove_offensive_message, bot_service),
    )
