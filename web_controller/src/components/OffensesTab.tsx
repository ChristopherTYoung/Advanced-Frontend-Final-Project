import { useGuilds } from '../hooks/useGuilds'
import { useOffenses } from '../hooks/useOffenses'
import { useState } from 'react'

export function OffensesTab() {
  const { data: guilds = [], isLoading: loadingGuilds } = useGuilds()
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null)
  
  const { 
    data: offenses = [], 
    isLoading: loadingOffenses, 
    refetch: refetchOffenses 
  } = useOffenses(selectedGuildId, !!selectedGuildId)

  return (
    <div className="messages-page">
      <div className="messages-card">
        <h1>Content Violations</h1>
        <p>View messages that were removed for violating content maturity rules</p>
        
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="guild-select" style={{ marginRight: '0.5rem' }}>Server:</label>
          <select
            id="guild-select"
            value={selectedGuildId || ''}
            onChange={(e) => setSelectedGuildId(e.target.value || null)}
            disabled={loadingGuilds}
            style={{ padding: '0.5rem', borderRadius: '4px' }}
          >
            <option value="">Select a server</option>
            {guilds.map((guild) => (
              <option key={guild.id} value={guild.id}>
                {guild.name}
              </option>
            ))}
          </select>
        </div>

        {selectedGuildId && (
          <button 
            className="refresh-btn"
            onClick={() => refetchOffenses()}
            disabled={loadingOffenses}
          >
            {loadingOffenses ? 'Refreshing...' : '🔄 Refresh'}
          </button>
        )}

        <div className="messages-list">
          {!selectedGuildId ? (
            <div className="no-messages">
              <p>Select a server to view violations</p>
            </div>
          ) : loadingOffenses ? (
            <div className="loading">Loading violations...</div>
          ) : offenses.length === 0 ? (
            <div className="no-messages">
              <p>No violations recorded</p>
              <p className="hint">Messages that violate content maturity rules will appear here</p>
            </div>
          ) : (
            offenses.map((offense) => (
              <div key={offense.offense_id} className="message-item user-message">
                <div className="message-header">
                  <span className="message-user">
                    🚫 User: {offense.username || 'Unknown User'}
                  </span>
                  <span className="message-time">
                    {offense.time_of_offense ? new Date(offense.time_of_offense || "").toLocaleString() : 'Unknown time'}
                  </span>
                </div>
                {offense.offensive_score !== null && offense.offensive_score !== undefined && (
                  <div style={{ 
                    padding: '0.25rem 0.5rem', 
                    marginBottom: '0.5rem',
                    backgroundColor: offense.offensive_score > 7 ? '#ff4444' : offense.offensive_score > 4 ? '#ff8844' : '#ffaa44',
                    borderRadius: '4px',
                    fontSize: '0.875rem',
                    fontWeight: 'bold'
                  }}>
                    Maturity Score: {offense.offensive_score}/10
                  </div>
                )}
                <div className="message-content">{offense.body?.replace(/<@\d+>/g, '').trim()}</div>
                {offense.picture && (
                  <div style={{ marginTop: '0.5rem' }}>
                    <img 
                      src={`data:image/png;base64,${offense.picture}`}
                      alt="Offensive content"
                      style={{ 
                        maxWidth: '300px', 
                        maxHeight: '300px',
                        borderRadius: '4px',
                        border: '1px solid #444'
                      }}
                    />
                  </div>
                )}
                <div className="message-meta">
                  Guild: {offense.guild_name || 'Unknown Guild'} • Channel: {offense.channel_name || 'Unknown Channel'}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
