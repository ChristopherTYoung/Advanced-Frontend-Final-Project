"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


# User schemas
class UserInfo(BaseModel):
    """User information from Discord OAuth."""

    id: str
    username: str
    avatar: str
    discriminator: str
    email: Optional[str] = None


# Guild schemas
class GuildInfo(BaseModel):
    """Guild (server) information."""

    id: str
    name: str
    icon: Optional[str] = None
    owner: Optional[bool] = None
    permissions: Optional[str] = None


# Channel schemas
class ChannelInfo(BaseModel):
    """Channel information."""

    id: str
    name: str
    type: Optional[int] = None


# Message schemas
class SendMessageRequest(BaseModel):
    guild_id: str = Field(..., description="Guild ID where the message will be sent")
    channel_id: str = Field(..., description="Channel ID where the message will be sent")
    message: Optional[str] = Field(None, min_length=1, max_length=2000, description="Raw message content")
    instructions: Optional[str] = Field(None, description="Optional instructions for the LLM to generate the message")
    event_details: Optional[str] = Field(
        None, description="Optional event details to include when generating the message"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Message cannot be empty or only whitespace")
        return v


class MessageInfo(BaseModel):
    """Message information from database."""

    id: str
    type: str
    content: str
    timestamp: str
    user_id: str
    username: str
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None


# Settings schemas
class BotSettings(BaseModel):
    """Bot settings for a guild."""

    personality: Optional[str] = Field(None, max_length=2000, description="Bot personality description")
    bot_nickname: Optional[str] = Field(None, max_length=32, description="Bot nickname in the server")

    @field_validator("bot_nickname")
    @classmethod
    def validate_nickname(cls, v: Optional[str]) -> Optional[str]:
        """Validate nickname length and content."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 32:
                raise ValueError("Nickname must be 32 characters or less")
        return v

    @field_validator("personality")
    @classmethod
    def validate_personality(cls, v: Optional[str]) -> Optional[str]:
        """Validate personality is not empty after stripping."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class Permission(BaseModel):
    permission_name: str
    allowed: bool


class Role(BaseModel):
    role_id: Optional[str] = None
    role_name: str
    permissions: list[Permission]


class RoleSettings(BaseModel):
    roles: Optional[list[Role]] = None


class ContentMaturityPreferences(BaseModel):
    """Content maturity rating preferences."""

    banned_content: Optional[list[str]] = Field(None, description="List of banned content phrases/topics")
    allowed_maturity_score: Optional[int] = Field(
        None, ge=0, le=10, description="Maximum allowed maturity score (0-10)"
    )


class SettingsContainer(BaseModel):
    """Container for bot and role settings stored in DB."""

    bot_settings: Optional[BotSettings] = None
    role_settings: Optional[RoleSettings] = None
    content_maturity_preferences: Optional[ContentMaturityPreferences] = None


class UpdateSettingsRequest(BaseModel):
    """Request to update guild bot settings."""

    settings: SettingsContainer = Field(..., description="Bot and role settings to update")


class GuildSettingsResponse(BaseModel):
    """Response containing guild settings."""

    guild_id: str
    settings: SettingsContainer | Dict[str, Any]
    edited_at: Optional[str] = None


# Response schemas
class SuccessResponse(BaseModel):
    """Generic success response."""

    ok: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Generic error response."""

    error: str
    detail: Optional[str] = None


class MessageSentResponse(SuccessResponse):
    """Response after sending a message."""

    message: str = "Message sent successfully"


class SettingsUpdatedResponse(SuccessResponse):
    """Response after updating settings."""

    message: str = "Settings updated successfully"
    guild_id: str


class SettingsDeletedResponse(SuccessResponse):
    """Response after deleting settings."""

    message: str = "Settings deleted successfully"
    guild_id: str


# Authentication responses
class AuthCallbackResponse(BaseModel):
    """Response from OAuth callback."""

    success: bool
    redirect_url: str


class MeResponse(BaseModel):
    """Response from /api/me endpoint."""

    user: Optional[UserInfo] = None


class LogoutResponse(BaseModel):
    """Response from logout endpoint."""

    ok: bool = True


# Guild responses
class GuildsResponse(BaseModel):
    """Response containing list of guilds."""

    guilds: list[GuildInfo]


class ChannelsResponse(BaseModel):
    """Response containing list of channels."""

    channels: list[ChannelInfo]


class MessagesResponse(BaseModel):
    """Response containing list of messages."""

    messages: list[MessageInfo]


# Event schemas
class EventCreateRequest(BaseModel):
    user_id: str = Field(..., description="User who created the event")
    time_of_event: datetime = Field(..., description="Timestamp for the event")
    event_name: str = Field(..., max_length=50)
    event_details: str = Field(..., max_length=200)


class EventInfo(BaseModel):
    event_id: int
    user_id: str
    guild_id: str
    time_of_event: datetime
    event_name: str
    event_details: str


class EventsResponse(BaseModel):
    events: list[EventInfo]


class ProposalCreateRequest(BaseModel):
    user_id: str = Field(..., description="User who proposed the event")
    time_of_event: datetime = Field(..., description="Proposed event timestamp")
    event_name: str = Field(..., max_length=50)
    event_details: str = Field(..., max_length=200)


class ProposalInfo(BaseModel):
    proposal_id: int
    user_id: str
    guild_id: str
    time_of_event: datetime
    event_name: str
    event_details: str
    created_at: Optional[datetime]
    approved: Optional[bool]
    time_approved: Optional[datetime]
    event_id: Optional[int]


class ProposalsResponse(BaseModel):
    proposals: list[ProposalInfo]
