import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { useGuilds, useGuildSettings, useUpdateGuildSettings, useGuildRoles } from '../hooks/useApi'

type RoleEntry = {
  role_id?: string;
  role_name: string;
  permissions: { permission_name: string; allowed: boolean }[];
}

export default function SettingsTab() {
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null)
  const [nickname, setNickname] = useState('')
  const [personality, setPersonality] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  const { data: guilds, isLoading: guildsLoading } = useGuilds()
  console.log('DEBUG: guilds data:', guilds)
  console.log('DEBUG: selectedGuildId:', selectedGuildId)
  const { data: settings, isLoading: settingsLoading } = useGuildSettings(selectedGuildId)
  const { data: guildRoles } = useGuildRoles(selectedGuildId)
  const updateSettings = useUpdateGuildSettings()

  useEffect(() => {
    if (settings?.settings) {
      const botSettings = settings.settings.bot_settings || {}
      const roleSettings = settings.settings.role_settings || { roles: [] }
      setNickname(botSettings.bot_nickname || '')
      setPersonality(botSettings.personality || '')
      setRoleEntries(roleSettings.roles || [])
    } else {
      setNickname('')
      setPersonality('')
      setRoleEntries([])
    }
  }, [settings])

  const [roleEntries, setRoleEntries] = useState<RoleEntry[]>([])
  const [selectedRoleToAdd, setSelectedRoleToAdd] = useState<string>('')

  const handleSave = async () => {
    if (!selectedGuildId) {
      setErrorMessage('Please select a guild first')
      return
    }

    setSuccessMessage('')
    setErrorMessage('')

    try {
      const payload: any = {
        bot_settings: {
          bot_nickname: nickname || undefined,
          personality: personality || undefined,
        },
      }
      if (isGuildOwner) {
        payload.role_settings = { roles: roleEntries }
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

  const permissionList = [
    'change_nickname',
    'change_personality',
    'make_events',
    'manage_proposals',
  ]

  const selectedGuildEntry = guilds?.find((g: any) => g.id === selectedGuildId)
  console.log('DEBUG: selectedGuildEntry FULL:', JSON.stringify(selectedGuildEntry, null, 2))
  console.log('DEBUG: owner value:', selectedGuildEntry?.owner, 'type:', typeof selectedGuildEntry?.owner)
  let isGuildOwner = false
  if (selectedGuildEntry) {
    if (selectedGuildEntry.owner) {
      isGuildOwner = true
    }
  }
  console.log('DEBUG: isGuildOwner:', isGuildOwner)

  function addSelectedRole() {
    if (!selectedRoleToAdd) return
    const roleId = selectedRoleToAdd
    const roleObj = guildRoles?.find((r: any) => r.id === roleId)
    const roleName = roleObj?.name || roleId
    if (roleEntries.find((r) => r.role_id === roleId || r.role_name === roleName)) return
    const newEntry: RoleEntry = {
      role_id: roleId,
      role_name: roleName,
      permissions: permissionList.map((p) => ({ permission_name: p, allowed: false })),
    }
    setRoleEntries((prev) => [...prev, newEntry])
  }

  function togglePermission(roleName: string, permissionName: string) {
    setRoleEntries((prev) =>
      prev.map((r) => {
        if (r.role_name !== roleName) return r
        return {
          ...r,
          permissions: r.permissions.map((p) =>
            p.permission_name === permissionName ? { ...p, allowed: !p.allowed } : p
          ),
        }
      })
    )
  }

  function removeRole(roleName: string) {
    setRoleEntries((prev) => prev.filter((r) => r.role_name !== roleName))
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

              <div className="form-group">
                <h3>Role Settings</h3>
                <label htmlFor="role-select">Add Role Permissions:</label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <select
                    id="role-select"
                    value={selectedRoleToAdd}
                    onChange={(e) => setSelectedRoleToAdd(e.target.value)}
                    disabled={!guildRoles || !isGuildOwner}
                  >
                    <option value="">-- Select a Role --</option>
                    {guildRoles?.map((r: any) => (
                      <option key={r.id} value={r.id}>{r.name}</option>
                    ))}
                  </select>
                  <button type="button" onClick={addSelectedRole} disabled={!isGuildOwner}>Add Role</button>
                </div>

                {!isGuildOwner && <p style={{ color: '#666' }}>Only the guild owner can edit role permissions.</p>}
                {roleEntries.length === 0 && <p>No roles configured yet.</p>}

                {roleEntries.map((role) => (
                  <div key={role.role_name} className="role-entry" style={{ border: '1px solid #ccc', padding: '8px', marginTop: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong>{role.role_name}</strong>
                      <button type="button" onClick={() => removeRole(role.role_name)} disabled={!isGuildOwner}>Remove</button>
                    </div>
                    <div style={{ display: 'flex', gap: '12px', marginTop: '8px', flexWrap: 'wrap' }}>
                      {role.permissions.map((p) => (
                        <label key={p.permission_name} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                          <input
                            type="checkbox"
                            checked={!!p.allowed}
                            onChange={() => togglePermission(role.role_name, p.permission_name)}
                            disabled={!isGuildOwner}
                          />
                          {p.permission_name}
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
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
