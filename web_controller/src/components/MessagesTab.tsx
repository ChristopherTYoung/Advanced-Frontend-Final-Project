import { useMessages } from '../hooks/useApi'

export function MessagesTab() {
  const { data: messages = [], isLoading: loadingMessages, refetch: refetchMessages } = useMessages(undefined, true)

  return (
    <div className="messages-page">
      <div className="messages-card">
        <h1>Bot Messages</h1>
        <p>View messages sent to your bot in server channels</p>
        
        <button 
          className="refresh-btn"
          onClick={() => refetchMessages()}
          disabled={loadingMessages}
        >
          {loadingMessages ? 'Refreshing...' : '🔄 Refresh Messages'}
        </button>

        <div className="messages-list">
          {loadingMessages ? (
            <div className="loading">Loading messages...</div>
          ) : messages.length === 0 ? (
            <div className="no-messages">
              <p>No messages yet</p>
              <p className="hint">Messages sent to your bot in server channels will appear here</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`message-item ${msg.type === 'sent' ? 'bot-message' : 'user-message'}`}>
                <div className="message-header">
                  <span className="message-user">
                    {msg.type === 'sent' ? '🤖 Bot' : msg.user_id || 'Unknown User'}
                  </span>
                  <span className="message-time">
                    {new Date(msg.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="message-content">{msg.content}</div>
                {msg.guild_id && msg.guild_id !== 'DM' && (
                  <div className="message-meta">
                    Guild: {msg.guild_id} • Channel: {msg.channel_id}
                  </div>
                )}
                {msg.guild_id === 'DM' && (
                  <div className="message-meta">
                    Direct Message
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
