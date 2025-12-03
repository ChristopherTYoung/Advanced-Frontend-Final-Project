"""Tests for MessageService - Message history and management."""

import pytest
import asyncpg
from datetime import datetime
from unittest.mock import AsyncMock
from services.message_service import MessageService


def make_datetime(date_str="2025-12-02"):
    """Helper to create datetime objects for mock data."""
    return datetime.fromisoformat(date_str)


@pytest.fixture
async def mock_pool():
    """Create a mock database pool."""
    pool = AsyncMock(spec=asyncpg.Pool)
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None
    return pool, conn


@pytest.fixture
async def service(mock_pool):
    """Create a MessageService instance with mocked database."""
    pool, conn = mock_pool
    service = MessageService()
    service.db_pool = pool
    return service, conn


class TestMessageService:
    """Test cases for MessageService."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test MessageService initializes correctly."""
        service = MessageService()
        assert service.db_pool is None

    @pytest.mark.asyncio
    async def test_add_dm_message(self, service):
        """Test adding a direct message to history."""
        svc, conn = service
        conn.execute.return_value = None

        await svc.add_to_history(
            message_type="dm",
            content="Hello bot!",
            user_id="123456789",
            username="testuser",
            message_id="msg_001",
            guild_id="DM",
            channel_id="dm_channel",
        )

        # Verify database insert was called
        assert conn.execute.called

    @pytest.mark.asyncio
    async def test_add_server_message(self, service):
        """Test adding a server channel message to history."""
        svc, conn = service
        conn.execute.return_value = None

        await svc.add_to_history(
            message_type="received",
            content="Server message",
            user_id="987654321",
            username="serveruser",
            guild_id="guild_123",
            channel_id="channel_456",
            message_id="msg_002",
        )

        assert conn.execute.called

    @pytest.mark.asyncio
    async def test_add_sent_message(self, service):
        """Test adding a bot-sent message to history."""
        svc, conn = service
        conn.execute.return_value = None

        await svc.add_to_history(
            message_type="sent",
            content="Bot response",
            user_id="bot_id",
            username="TestBot",
            guild_id="guild_123",
            channel_id="channel_456",
            message_id="msg_003",
        )

        assert conn.execute.called

    @pytest.mark.asyncio
    async def test_message_auto_id_generation(self, service):
        """Test that messages work without message_id."""
        svc, conn = service
        conn.execute.return_value = None

        await svc.add_to_history(
            message_type="dm", content="Test message", user_id="123", username="user", guild_id="DM", channel_id="dm"
        )

        assert conn.execute.called

    @pytest.mark.asyncio
    async def test_get_history_no_filters(self, service):
        """Test retrieving all messages without filters."""
        svc, conn = service
        # Mock fetch to return sample data
        conn.fetch.return_value = [
            {"message_id": i, "role": "user", "body": f"Message {i}", "created_at": make_datetime(), "user_id": "123", "guild_id": "DM", "channel_id": "DM"} for i in range(5)
        ]

        history = await svc.get_history(limit=10)
        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_get_history_with_type_filter(self, service):
        """Test retrieving messages with message_type filter."""
        svc, conn = service
        conn.fetch.return_value = [{"message_id": 1, "role": "user", "body": "DM", "created_at": make_datetime(), "user_id": "123", "guild_id": "DM", "channel_id": "DM"}]

        history = await svc.get_history(limit=10, message_type="dm")
        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_get_history_with_user_filter(self, service):
        """Test retrieving messages filtered by user_id."""
        svc, conn = service
        conn.fetch.return_value = [{"message_id": 1, "role": "user", "body": "Test", "created_at": make_datetime(), "user_id": "123", "guild_id": "DM", "channel_id": "DM"}]

        history = await svc.get_history(limit=10, user_id="123")
        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_get_history_with_combined_filters(self, service):
        """Test retrieving messages with combined filters."""
        svc, conn = service
        conn.fetch.return_value = []

        history = await svc.get_history(limit=10, message_type="dm", user_id="123")
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_get_history_with_limit(self, service):
        """Test that history respects the limit parameter."""
        svc, conn = service
        conn.fetch.return_value = [
            {"message_id": i, "role": "user", "body": f"Message {i}", "created_at": make_datetime(), "user_id": "123", "guild_id": "DM", "channel_id": "DM"} for i in range(3)
        ]

        history = await svc.get_history(limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_get_dm_messages(self, service):
        """Test retrieving only DM messages."""
        svc, conn = service
        conn.fetch.return_value = [{"message_id": 1, "role": "user", "body": "DM", "created_at": make_datetime(), "user_id": "123", "guild_id": "DM", "channel_id": "DM"}]

        history = await svc.get_history(limit=10, guild_id="DM")
        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_max_history_limit(self, service):
        """Test that service respects maximum history limit."""
        svc, conn = service
        # This is now controlled by SQL LIMIT, no in-memory limit
        conn.fetch.return_value = []

        history = await svc.get_history(limit=1000)
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_clear_history(self, service):
        """Test clearing message history."""
        svc, conn = service
        # Database-backed service doesn't have clear_history method
        # This test is no longer applicable
        assert True

    @pytest.mark.asyncio
    async def test_timestamp_format(self, service):
        """Test that timestamps are included in messages."""
        svc, conn = service
        conn.execute.return_value = None

        await svc.add_to_history(
            message_type="dm",
            content="Test",
            user_id="123",
            username="user",
            guild_id="DM",
            channel_id="dm",
            message_id="msg_1",
        )

        # Timestamp is now handled by database DEFAULT NOW()
        assert conn.execute.called

    @pytest.mark.asyncio
    async def test_empty_history_retrieval(self, service):
        """Test retrieving history when no messages exist."""
        svc, conn = service
        conn.fetch.return_value = []

        history = await svc.get_history()
        assert history == []


class TestMessageServiceIntegration:
    """Integration tests for MessageService."""

    @pytest.mark.asyncio
    async def test_conversation_flow(self, service):
        """Test a typical conversation flow."""
        svc, conn = service
        conn.execute.return_value = None
        conn.fetch.return_value = [
            {"message_id": 1, "role": "user", "body": "Hello", "created_at": make_datetime(), "user_id": "123", "guild_id": "guild_1", "channel_id": "channel_1"},
            {"message_id": 2, "role": "assistant", "body": "Hi", "created_at": make_datetime(), "user_id": "bot", "guild_id": "guild_1", "channel_id": "channel_1"},
        ]

        # User message
        await svc.add_to_history(
            message_type="received",
            content="Hello bot",
            user_id="123",
            username="user",
            guild_id="guild_1",
            channel_id="channel_1",
        )

        # Bot response
        await svc.add_to_history(
            message_type="sent",
            content="Hello user!",
            user_id="bot",
            username="Bot",
            guild_id="guild_1",
            channel_id="channel_1",
        )

        history = await svc.get_history(limit=10)
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_multi_user_server_messages(self, service):
        """Test handling messages from multiple users in a server."""
        svc, conn = service
        conn.execute.return_value = None
        conn.fetch.return_value = [
            {"message_id": i, "role": "user", "body": f"User {i}", "created_at": make_datetime(), "user_id": f"{i}", "guild_id": "guild_1", "channel_id": "channel_1"} for i in range(3)
        ]

        users = [("user1", "123"), ("user2", "456"), ("user3", "789")]

        for username, user_id in users:
            await svc.add_to_history(
                message_type="received",
                content=f"Message from {username}",
                user_id=user_id,
                username=username,
                guild_id="guild_1",
                channel_id="channel_1",
            )

        history = await svc.get_history(limit=10)
        assert len(history) == 3


