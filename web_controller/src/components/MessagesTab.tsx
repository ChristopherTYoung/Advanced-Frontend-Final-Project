import { useMessages } from '../hooks/useMessages'
import { MessageItem } from './MessageItem'
import { EmptyState } from './EmptyState'
import { LoadingState } from './LoadingState'

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
            <LoadingState message="Loading messages..." />
          ) : messages.length === 0 ? (
            <EmptyState
              message="No messages yet"
              hint="Messages sent to your bot in server channels will appear here"
            />
          ) : (
            messages.map((msg) => (
              <MessageItem
                key={msg.id}
                username={msg.username || 'Unknown User'}
                timestamp={msg.timestamp}
                content={msg.content}
                guildName={msg.guild_name}
                channelName={msg.channel_name}
                isDM={msg.guild_id === 'DM'}
                isBot={msg.type === 'sent'}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
