import { useState, useEffect } from 'react'
import { useGuilds, useChannels, useSendMessage } from '../hooks/useApi'

interface TestTabProps {
  user: {
    id?: string
    username?: string
  }
}

export function TestTab({ user }: TestTabProps) {
  const [selectedServer, setSelectedServer] = useState<string>('')
  const [selectedChannel, setSelectedChannel] = useState<string>('')
  const [message, setMessage] = useState<string>('')
  const [responseMessage, setResponseMessage] = useState<string>('')

  const { data: guilds = [] } = useGuilds(true)
  const { data: channels = [] } = useChannels(selectedServer, true)
  const sendMessageMutation = useSendMessage()

  // Reset channel selection when server changes
  useEffect(() => {
    if (!selectedServer) {
      setSelectedChannel('')
    }
  }, [selectedServer])

  const handleSendMessage = async () => {
    if (!selectedServer || !selectedChannel || !message) return
    
    setResponseMessage('')
    
    try {
      await sendMessageMutation.mutateAsync({
        guildId: selectedServer,
        channelId: selectedChannel,
        message: message,
        userId: user?.id,
        username: user?.username
      })
      
      setResponseMessage('✅ Message sent successfully!')
      setMessage('')
    } catch (error) {
      setResponseMessage(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  return (
    <div className="test-page">
      <div className="test-card">
        <h1>Test Bot Messages</h1>
        <p>Send a test message to any channel in your Discord servers.</p>
        
        <div className="form-group">
          <label htmlFor="server-select">Select Server:</label>
          <select 
            id="server-select"
            className="select-control"
            value={selectedServer}
            onChange={(e) => {
              setSelectedServer(e.target.value)
              setSelectedChannel('')
            }}
          >
            <option value="">-- Choose a server --</option>
            {guilds.map(server => (
              <option key={server.id} value={server.id}>
                {server.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="channel-select">Select Channel:</label>
          <select 
            id="channel-select"
            className="select-control"
            value={selectedChannel}
            onChange={(e) => setSelectedChannel(e.target.value)}
            disabled={!selectedServer || channels.length === 0}
          >
            <option value="">-- Choose a channel --</option>
            {channels.map(channel => (
              <option key={channel.id} value={channel.id}>
                #{channel.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="message-input">Message:</label>
          <textarea 
            id="message-input"
            className="message-input"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message here..."
            rows={4}
          />
        </div>

        <button 
          className="send-btn"
          onClick={handleSendMessage}
          disabled={sendMessageMutation.isPending || !selectedServer || !selectedChannel || !message.trim()}
        >
          {sendMessageMutation.isPending ? 'Sending...' : 'Send Message'}
        </button>

        {responseMessage && (
          <div className={`response-message ${responseMessage.startsWith('❌') ? 'error' : 'success'}`}>
            {responseMessage}
          </div>
        )}
      </div>
    </div>
  )
}
