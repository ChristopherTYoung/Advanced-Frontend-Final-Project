import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { GuildSettingsSchema, UpdateGuildSettingsRequestSchema, type GuildSettings, type BotSettings, type RoleSettings, type ContentMaturityPreferences } from '../schemas'
import { api } from '../utils/api'

async function fetchGuildSettings(guildId: string): Promise<GuildSettings> {
  const response = await fetch(api(`/api/guilds/${guildId}/settings`), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch guild settings')
  }
  const data = await response.json()
  return GuildSettingsSchema.parse(data)
}

async function updateGuildSettings(
  guildId: string, 
  settings: { 
    bot_settings?: BotSettings
    role_settings?: RoleSettings
    content_maturity_preferences?: ContentMaturityPreferences 
  }
) {
  const validated = UpdateGuildSettingsRequestSchema.parse({ settings })

  const response = await fetch(api(`/api/guilds/${guildId}/settings`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(validated),
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || 'Failed to update settings')
  }
  return data
}

export function useGuildSettings(guildId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['guildSettings', guildId],
    queryFn: () => fetchGuildSettings(guildId!),
    enabled: enabled && !!guildId,
  })
}

export function useUpdateGuildSettings() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ 
      guildId, 
      settings 
    }: { 
      guildId: string
      settings: { 
        bot_settings?: BotSettings
        role_settings?: RoleSettings
        content_maturity_preferences?: ContentMaturityPreferences 
      } 
    }) => updateGuildSettings(guildId, settings),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['guildSettings', variables.guildId] })
    },
  })
}
