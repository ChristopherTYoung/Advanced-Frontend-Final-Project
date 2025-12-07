import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { GuildSchema, type Guild } from '../schemas'
import { api } from '../utils/api'

async function fetchGuilds(): Promise<Guild[]> {
  const response = await fetch(api('/api/guilds'), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch guilds')
  }
  const data = await response.json()
  const guildsArray = data.guilds || []
  return z.array(GuildSchema).parse(guildsArray)
}

async function fetchGuildRoles(guildId: string) {
  const response = await fetch(api(`/api/guilds/${guildId}/roles`), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch guild roles')
  }
  const data = await response.json()
  return data.roles || []
}

async function fetchUserPermissions(guildId: string) {
  const response = await fetch(api(`/api/guilds/${guildId}/user/permissions`), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch user permissions')
  }
  const data = await response.json()
  return data
}

export function useGuilds(enabled: boolean = true) {
  return useQuery({
    queryKey: ['guilds'],
    queryFn: fetchGuilds,
    enabled,
  })
}

export function useGuildRoles(guildId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['guildRoles', guildId],
    queryFn: () => fetchGuildRoles(guildId!),
    enabled: enabled && !!guildId,
  })
}

export function useUserPermissions(guildId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['userPermissions', guildId],
    queryFn: () => fetchUserPermissions(guildId!),
    enabled: enabled && !!guildId,
  })
}
