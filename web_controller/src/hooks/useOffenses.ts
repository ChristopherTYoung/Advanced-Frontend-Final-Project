import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { OffenseSchema, type Offense } from '../schemas'
import { api } from '../utils/api'

async function fetchOffenses(guildId: string): Promise<Offense[]> {
  const response = await fetch(api(`/api/guilds/${guildId}/offenses`), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch offenses')
  }
  const data = await response.json()
  const offensesArray = data.offenses || []
  return z.array(OffenseSchema).parse(offensesArray)
}

export function useOffenses(guildId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['offenses', guildId],
    queryFn: () => fetchOffenses(guildId!),
    enabled: enabled && !!guildId,
  })
}
