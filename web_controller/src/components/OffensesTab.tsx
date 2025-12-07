import { useGuilds } from '../hooks/useGuilds'
import { useOffenses } from '../hooks/useOffenses'
import { useState } from 'react'
import { GuildSelector } from './GuildSelector'
import { MessageItem } from './MessageItem'
import { EmptyState } from './EmptyState'
import { LoadingState } from './LoadingState'

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
        
        <GuildSelector
          selectedGuildId={selectedGuildId}
          onGuildChange={setSelectedGuildId}
          guilds={guilds}
          isLoading={loadingGuilds}
          label="Server:"
          placeholder="Select a server"
        />

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
            <EmptyState message="Select a server to view violations" />
          ) : loadingOffenses ? (
            <LoadingState message="Loading violations..." />
          ) : offenses.length === 0 ? (
            <EmptyState
              message="No violations recorded"
              hint="Messages that violate content maturity rules will appear here"
            />
          ) : (
            offenses.map((offense) => (
              <MessageItem
                key={offense.offense_id}
                username={`🚫 User: ${offense.username || 'Unknown User'}`}
                timestamp={offense.time_of_offense || ''}
                content={offense.body || ''}
                guildName={offense.guild_name}
                channelName={offense.channel_name}
                maturityScore={offense.offensive_score}
                picture={offense.picture}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
