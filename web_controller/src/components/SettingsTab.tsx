import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { useGuilds, useGuildSettings, useUpdateGuildSettings } from '../hooks/useApi'

export default function SettingsTab() {
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null)
  const [nickname, setNickname] = useState('')
  const [personality, setPersonality] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  const { data: guilds, isLoading: guildsLoading } = useGuilds()
  const { data: settings, isLoading: settingsLoading } = useGuildSettings(selectedGuildId)
  const updateSettings = useUpdateGuildSettings()

  // Update form fields when settings load
  useEffect(() => {
    if (settings?.settings) {
      setNickname(settings.settings.bot_nickname || '')
      setPersonality(settings.settings.personality || '')
    } else {
      setNickname('')
      setPersonality('')
    }
  }, [settings])

  const handleSave = async () => {
    if (!selectedGuildId) {
      setErrorMessage('Please select a guild first')
      return
    }

    setSuccessMessage('')
    setErrorMessage('')

    try {
      await updateSettings.mutateAsync({
        guildId: selectedGuildId,
        settings: {
          bot_nickname: nickname || undefined,
          personality: personality || undefined,
        },
      })
      toast.success('Settings saved successfully!')
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to save settings')
    }
  }

  return (
    <div className="settings-tab">
      <h2>Bot Settings</h2>
      
      <div className="form-group">
        <label htmlFor="guild-select">Select Guild:</label>
        <select
          id="guild-select"
          value={selectedGuildId || ''}
          onChange={(e) => setSelectedGuildId(e.target.value || null)}
          disabled={guildsLoading}
        >
          <option value="">-- Select a Guild --</option>
          {guilds?.map((guild) => (
            <option key={guild.id} value={guild.id}>
              {guild.name}
            </option>
          ))}
        </select>
      </div>

      {selectedGuildId && (
        <>
          {settingsLoading ? (
            <p>Loading settings...</p>
          ) : (
            <>
              <div className="form-group">
                <label htmlFor="nickname">Bot Nickname:</label>
                <input
                  id="nickname"
                  type="text"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="Enter bot nickname (max 32 characters)"
                  maxLength={32}
                />
                <small>Leave empty to use default bot username</small>
              </div>

              <div className="form-group">
                <label htmlFor="personality">Bot Personality:</label>
                <textarea
                  id="personality"
                  value={personality}
                  onChange={(e) => setPersonality(e.target.value)}
                  placeholder="Enter bot personality description..."
                  rows={6}
                />
                <small>
                  Example: "You are a friendly and helpful assistant. You love to make jokes and use emojis."
                </small>
              </div>

              <button
                onClick={handleSave}
                disabled={updateSettings.isPending}
                className="save-button"
              >
                {updateSettings.isPending ? 'Saving...' : 'Save Settings'}
              </button>

              {successMessage && <div className="success-message">{successMessage}</div>}
              {errorMessage && <div className="error-message">{errorMessage}</div>}
            </>
          )}
        </>
      )}
    </div>
  )
}
