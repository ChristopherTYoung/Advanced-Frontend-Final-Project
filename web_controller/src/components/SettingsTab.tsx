import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { useGuilds, useUserPermissions } from '../hooks/useGuilds'
import { useGuildSettings, useUpdateGuildSettings } from '../hooks/useSettings'
import type { RoleSettings as RoleSettingsType, ContentMaturityPreferences } from '../schemas'
import { RoleSettings } from './RoleSettings'
import { BotSettings } from './BotSettings'
import { MaturitySettings } from './MaturitySettings'
import { GuildSelector } from './GuildSelector'

type RoleEntry = {
  role_id?: string;
  role_name: string;
  permissions: { permission_name: string; allowed: boolean }[];
}

type SettingsSubTab = 'bot' | 'roles' | 'maturity'

export default function SettingsTab() {
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null)
  const [activeSubTab, setActiveSubTab] = useState<SettingsSubTab>('bot')
  const [nickname, setNickname] = useState('')
  const [personality, setPersonality] = useState('')
  const [bannedContent, setBannedContent] = useState<string[]>([])
  const [allowedMaturityScore, setAllowedMaturityScore] = useState(5)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  const { data: guilds, isLoading: guildsLoading } = useGuilds()
  const { data: settings, isLoading: settingsLoading } = useGuildSettings(selectedGuildId)
  const { data: userPermissions } = useUserPermissions(selectedGuildId)
  const updateSettings = useUpdateGuildSettings()

  useEffect(() => {
    if (settings?.settings) {
      const botSettings = settings.settings.bot_settings || {}
      const roleSettings = settings.settings.role_settings || { roles: [] }
      const maturityPrefs = settings.settings.content_maturity_preferences || {}
      setNickname(botSettings.bot_nickname || '')
      setPersonality(botSettings.personality || '')
      setRoleEntries(roleSettings.roles || [])
      setBannedContent(maturityPrefs.banned_content || [])
      setAllowedMaturityScore(maturityPrefs.allowed_maturity_score ?? 5)
    } else {
      setNickname('')
      setPersonality('')
      setRoleEntries([])
      setBannedContent([])
      setAllowedMaturityScore(5)
    }
  }, [settings])

  const [roleEntries, setRoleEntries] = useState<RoleEntry[]>([])

  const handleSave = async () => {
    if (!selectedGuildId) {
      setErrorMessage('Please select a guild first')
      return
    }

    setSuccessMessage('')
    setErrorMessage('')

    try {
      const payload: { bot_settings: { bot_nickname?: string; personality?: string }; role_settings?: RoleSettingsType; content_maturity_preferences?: ContentMaturityPreferences } = {
        bot_settings: {
          bot_nickname: nickname || undefined,
          personality: personality || undefined,
        },
      }
      if (isGuildOwner) {
        payload.role_settings = { roles: roleEntries }
        payload.content_maturity_preferences = {
          banned_content: bannedContent.filter(c => c.trim() !== ''),
          allowed_maturity_score: allowedMaturityScore,
        }
      }

      await updateSettings.mutateAsync({
        guildId: selectedGuildId,
        settings: payload,
      })
      toast.success('Settings saved successfully!')
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to save settings')
    }
  }

  const isGuildOwner = userPermissions?.is_owner || false
  const canChangeNickname = userPermissions?.permissions?.change_nickname || false
  const canChangePersonality = userPermissions?.permissions?.change_personality || false

  const renderSubTabContent = () => {
    switch (activeSubTab) {
      case 'bot':
        return (
          <BotSettings
            nickname={nickname}
            setNickname={setNickname}
            canChangeNickname={canChangeNickname}
            personality={personality}
            setPersonality={setPersonality}
            canChangePersonality={canChangePersonality}
          />
        )
      case 'roles':
        return (
          <RoleSettings
            selectedGuildId={selectedGuildId}
            roleEntries={roleEntries}
            setRoleEntries={setRoleEntries}
            isGuildOwner={isGuildOwner}
          />
        )
      case 'maturity':
        return (
          <MaturitySettings
            bannedContent={bannedContent}
            setBannedContent={setBannedContent}
            allowedMaturityScore={allowedMaturityScore}
            setAllowedMaturityScore={setAllowedMaturityScore}
            isGuildOwner={isGuildOwner}
          />
        )
    }
  }

  return (
    <div className="settings-tab">
      <GuildSelector
        selectedGuildId={selectedGuildId}
        onGuildChange={setSelectedGuildId}
        guilds={guilds || []}
        isLoading={guildsLoading}
        label="Select Guild:"
      />

      {selectedGuildId && (
        <>
          {settingsLoading ? (
            <p>Loading settings...</p>
          ) : (
            <>
              <div className="settings-sub-tabs">
                <button
                  className={`sub-tab-button ${activeSubTab === 'bot' ? 'active' : ''}`}
                  onClick={() => setActiveSubTab('bot')}
                >
                  Bot Personality
                </button>
                <button
                  className={`sub-tab-button ${activeSubTab === 'roles' ? 'active' : ''}`}
                  onClick={() => setActiveSubTab('roles')}
                  disabled={!isGuildOwner}
                  title={!isGuildOwner ? 'Only guild owners can manage roles' : ''}
                >
                  Role Settings
                </button>
                <button
                  className={`sub-tab-button ${activeSubTab === 'maturity' ? 'active' : ''}`}
                  onClick={() => setActiveSubTab('maturity')}
                  disabled={!isGuildOwner}
                  title={!isGuildOwner ? 'Only guild owners can manage maturity settings' : ''}
                >
                  Maturity Preferences
                </button>
              </div>

              <div className="settings-sub-content">
                {renderSubTabContent()}
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
