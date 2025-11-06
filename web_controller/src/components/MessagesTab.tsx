import { useMessages } from '../hooks/useApi'

export function MessagesTab() {
  const { data: messages = [], isLoading: loadingMessages, refetch: refetchMessages } = useMessages('received', true)

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
              <div key={msg.id} className="message-item">
                <div className="message-header">
                  <span className="message-user">{msg.username}</span>
                  <span className="message-time">
                    {new Date(msg.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="message-content">{msg.content}</div>
                {msg.guild_name && (
                  <div className="message-meta">
                    Server: {msg.guild_name} • Channel: #{msg.channel_name}
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
