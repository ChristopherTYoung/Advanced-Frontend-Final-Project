interface MessageItemProps {
  username: string
  timestamp: string
  content: string
  guildName?: string | null
  channelName?: string | null
  isDM?: boolean
  isBot?: boolean
  maturityScore?: number | null
  picture?: string | null
}

export function MessageItem({
  username,
  timestamp,
  content,
  guildName,
  channelName,
  isDM = false,
  isBot = false,
  maturityScore,
  picture,
}: MessageItemProps) {
  const cleanContent = content.replace(/<@\d+>/g, '').trim()

  return (
    <div className={`message-item ${isBot ? 'bot-message' : 'user-message'}`}>
      <div className="message-header">
        <span className="message-user">
          {isBot ? '🤖 Bot' : username}
        </span>
        <span className="message-time">
          {new Date(timestamp).toLocaleString()}
        </span>
      </div>

      {maturityScore !== null && maturityScore !== undefined && (
        <div
          style={{
            padding: '0.25rem 0.5rem',
            marginBottom: '0.5rem',
            backgroundColor:
              maturityScore > 7 ? '#ff4444' : maturityScore > 4 ? '#ff8844' : '#ffaa44',
            borderRadius: '4px',
            fontSize: '0.875rem',
            fontWeight: 'bold',
          }}
        >
          Maturity Score: {maturityScore}/10
        </div>
      )}

      <div className="message-content">{cleanContent}</div>

      {picture && (
        <div style={{ marginTop: '0.5rem' }}>
          <img
            src={`data:image/png;base64,${picture}`}
            alt="Offensive content"
            style={{
              maxWidth: '300px',
              maxHeight: '300px',
              borderRadius: '4px',
              border: '1px solid #444',
            }}
          />
        </div>
      )}

      {isDM ? (
        <div className="message-meta">Direct Message</div>
      ) : guildName || channelName ? (
        <div className="message-meta">
          Guild: {guildName || 'Unknown Guild'} • Channel: {channelName || 'Unknown Channel'}
        </div>
      ) : null}
    </div>
  )
}
