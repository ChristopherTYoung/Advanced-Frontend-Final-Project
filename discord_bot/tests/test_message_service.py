"""Tests for MessageService - Message history and management."""
import pytest
from datetime import datetime
from services.message_service import MessageService


class TestMessageService:
    """Test cases for MessageService."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh MessageService instance for each test."""
        return MessageService()
    
    def test_initialization(self, service):
        """Test MessageService initializes correctly."""
        assert service.message_history == []
        assert service.max_history == 100
    
    def test_add_dm_message(self, service):
        """Test adding a direct message to history."""
        service.add_to_history(
            message_type='dm',
            content='Hello bot!',
            user_id='123456789',
            username='testuser',
            message_id='msg_001'
        )
        
        assert len(service.message_history) == 1
        message = service.message_history[0]
        
        assert message['type'] == 'dm'
        assert message['content'] == 'Hello bot!'
        assert message['user_id'] == '123456789'
        assert message['username'] == 'testuser'
        assert message['id'] == 'msg_001'
        assert 'timestamp' in message
    
    def test_add_server_message(self, service):
        """Test adding a server channel message to history."""
        service.add_to_history(
            message_type='received',
            content='Server message',
            user_id='987654321',
            username='serveruser',
            guild_id='guild_123',
            guild_name='Test Server',
            channel_id='channel_456',
            channel_name='general',
            message_id='msg_002'
        )
        
        assert len(service.message_history) == 1
        message = service.message_history[0]
        
        assert message['type'] == 'received'
        assert message['content'] == 'Server message'
        assert message['guild_id'] == 'guild_123'
        assert message['guild_name'] == 'Test Server'
        assert message['channel_id'] == 'channel_456'
        assert message['channel_name'] == 'general'
    
    def test_add_sent_message(self, service):
        """Test adding a bot-sent message to history."""
        service.add_to_history(
            message_type='sent',
            content='Bot response',
            user_id='bot_id',
            username='TestBot',
            guild_id='guild_123',
            channel_id='channel_456',
            message_id='msg_003'
        )
        
        assert len(service.message_history) == 1
        message = service.message_history[0]
        assert message['type'] == 'sent'
        assert message['content'] == 'Bot response'
    
    def test_message_auto_id_generation(self, service):
        """Test that messages get auto-generated IDs if not provided."""
        service.add_to_history(
            message_type='dm',
            content='Test message',
            user_id='123',
            username='user'
        )
        
        message = service.message_history[0]
        assert message['id'] is not None
        assert isinstance(message['id'], str)
    
    def test_get_history_no_filters(self, service):
        """Test retrieving all messages without filters."""
        # Add multiple messages
        for i in range(5):
            service.add_to_history(
                message_type='dm',
                content=f'Message {i}',
                user_id='123',
                username='user',
                message_id=f'msg_{i}'
            )
        
        history = service.get_history()
        assert len(history) == 5
        # Should be in reverse order (newest first)
        assert history[0]['content'] == 'Message 4'
        assert history[4]['content'] == 'Message 0'
    
    def test_get_history_with_type_filter(self, service):
        """Test filtering messages by type."""
        service.add_to_history(message_type='dm', content='DM 1', user_id='1', username='user1')
        service.add_to_history(message_type='sent', content='Sent 1', user_id='2', username='bot')
        service.add_to_history(message_type='dm', content='DM 2', user_id='1', username='user1')
        service.add_to_history(message_type='received', content='Server 1', user_id='3', username='user3')
        
        dm_messages = service.get_history(message_type='dm')
        assert len(dm_messages) == 2
        assert all(m['type'] == 'dm' for m in dm_messages)
        
        sent_messages = service.get_history(message_type='sent')
        assert len(sent_messages) == 1
        assert sent_messages[0]['content'] == 'Sent 1'
    
    def test_get_history_with_user_filter(self, service):
        """Test filtering messages by user ID."""
        service.add_to_history(message_type='dm', content='User 1 msg', user_id='user_1', username='alice')
        service.add_to_history(message_type='dm', content='User 2 msg', user_id='user_2', username='bob')
        service.add_to_history(message_type='dm', content='User 1 msg 2', user_id='user_1', username='alice')
        
        user1_messages = service.get_history(user_id='user_1')
        assert len(user1_messages) == 2
        assert all(m['user_id'] == 'user_1' for m in user1_messages)
    
    def test_get_history_with_combined_filters(self, service):
        """Test filtering messages by both type and user."""
        service.add_to_history(message_type='dm', content='DM from user1', user_id='user_1', username='alice')
        service.add_to_history(message_type='sent', content='Sent to user1', user_id='user_1', username='alice')
        service.add_to_history(message_type='dm', content='DM from user2', user_id='user_2', username='bob')
        
        filtered = service.get_history(message_type='dm', user_id='user_1')
        assert len(filtered) == 1
        assert filtered[0]['content'] == 'DM from user1'
    
    def test_get_history_with_limit(self, service):
        """Test limiting the number of returned messages."""
        for i in range(10):
            service.add_to_history(message_type='dm', content=f'Message {i}', user_id='123', username='user')
        
        history = service.get_history(limit=5)
        assert len(history) == 5
        # Should return the 5 most recent
        assert history[0]['content'] == 'Message 9'
        assert history[4]['content'] == 'Message 5'
    
    def test_get_dm_messages(self, service):
        """Test the DM-specific convenience method."""
        service.add_to_history(message_type='dm', content='DM 1', user_id='1', username='user1')
        service.add_to_history(message_type='sent', content='Sent 1', user_id='2', username='bot')
        service.add_to_history(message_type='dm', content='DM 2', user_id='1', username='user1')
        
        dm_messages = service.get_dm_messages()
        assert len(dm_messages) == 2
        assert all(m['type'] == 'dm' for m in dm_messages)
    
    def test_max_history_limit(self, service):
        """Test that message history is capped at max_history."""
        # Add more than max_history messages
        for i in range(150):
            service.add_to_history(
                message_type='dm',
                content=f'Message {i}',
                user_id='123',
                username='user',
                message_id=f'msg_{i}'
            )
        
        # Should only keep the last 100
        assert len(service.message_history) == 100
        # First message should be #50 (0-49 were dropped)
        assert service.message_history[0]['content'] == 'Message 50'
        # Last message should be #149
        assert service.message_history[-1]['content'] == 'Message 149'
    
    def test_clear_history(self, service):
        """Test clearing all message history."""
        for i in range(5):
            service.add_to_history(message_type='dm', content=f'Message {i}', user_id='123', username='user')
        
        assert len(service.message_history) == 5
        
        service.clear_history()
        
        assert len(service.message_history) == 0
        assert service.get_history() == []
    
    def test_timestamp_format(self, service):
        """Test that timestamps are in ISO format."""
        service.add_to_history(
            message_type='dm',
            content='Test',
            user_id='123',
            username='user'
        )
        
        message = service.message_history[0]
        timestamp = message['timestamp']
        
        # Should be able to parse as ISO format
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)
    
    def test_empty_history_retrieval(self, service):
        """Test retrieving from empty history."""
        assert service.get_history() == []
        assert service.get_dm_messages() == []
        assert service.get_history(message_type='sent') == []


class TestMessageServiceIntegration:
    """Integration tests for MessageService with realistic scenarios."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh MessageService instance for each test."""
        return MessageService()
    
    def test_conversation_flow(self, service):
        """Test a realistic conversation flow."""
        # User sends DM
        service.add_to_history(
            message_type='dm',
            content='Hello bot!',
            user_id='user_123',
            username='alice',
            message_id='msg_1'
        )
        
        # Bot sends response
        service.add_to_history(
            message_type='sent',
            content='Hi alice! How can I help?',
            user_id='bot_id',
            username='TestBot',
            message_id='msg_2'
        )
        
        # User sends another DM
        service.add_to_history(
            message_type='dm',
            content='Tell me a joke',
            user_id='user_123',
            username='alice',
            message_id='msg_3'
        )
        
        # Verify conversation history
        all_messages = service.get_history()
        assert len(all_messages) == 3
        
        # Verify DM messages only
        dm_messages = service.get_dm_messages()
        assert len(dm_messages) == 2
        assert dm_messages[0]['content'] == 'Tell me a joke'
        assert dm_messages[1]['content'] == 'Hello bot!'
    
    def test_multi_user_server_messages(self, service):
        """Test messages from multiple users in a server."""
        users = [
            ('user_1', 'alice'),
            ('user_2', 'bob'),
            ('user_3', 'charlie')
        ]
        
        for user_id, username in users:
            service.add_to_history(
                message_type='received',
                content=f'Message from {username}',
                user_id=user_id,
                username=username,
                guild_id='guild_123',
                guild_name='Test Server',
                channel_id='channel_456',
                channel_name='general'
            )
        
        # Get all server messages
        server_messages = service.get_history(message_type='received')
        assert len(server_messages) == 3
        
        # Get messages from specific user
        alice_messages = service.get_history(user_id='user_1')
        assert len(alice_messages) == 1
        assert alice_messages[0]['username'] == 'alice'
