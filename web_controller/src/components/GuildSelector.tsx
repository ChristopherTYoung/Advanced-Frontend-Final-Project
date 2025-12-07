import type { Guild } from '../schemas'

interface GuildSelectorProps {
  selectedGuildId: string | null
  onGuildChange: (guildId: string | null) => void
  guilds: Guild[]
  isLoading?: boolean
  label?: string
  placeholder?: string
  className?: string
}

export function GuildSelector({
  selectedGuildId,
  onGuildChange,
  guilds,
  isLoading = false,
  label = 'Guild:',
  placeholder = '-- Select a Guild --',
  className = 'form-group',
}: GuildSelectorProps) {
  return (
    <div className={className}>
      <label htmlFor="guild-select">{label}</label>
      <select
        id="guild-select"
        value={selectedGuildId || ''}
        onChange={(e) => onGuildChange(e.target.value || null)}
        disabled={isLoading}
      >
        <option value="">{placeholder}</option>
        {guilds.map((guild) => (
          <option key={guild.id} value={guild.id}>
            {guild.name}
          </option>
        ))}
      </select>
    </div>
  )
}
