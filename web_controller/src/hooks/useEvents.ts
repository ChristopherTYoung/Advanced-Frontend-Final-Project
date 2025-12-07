import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { EventSchema, EventCreateRequestSchema, type Event, type EventCreateRequest } from '../schemas'
import { api } from '../utils/api'

async function fetchEvents(guildId: string): Promise<Event[]> {
  const response = await fetch(api(`/api/guilds/${guildId}/events`), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch events')
  }
  const data = await response.json()
  const eventsArray = data.events || []
  return z.array(EventSchema).parse(eventsArray)
}

async function createEvent(params: { guildId: string; payload: EventCreateRequest }) {
  const validated = EventCreateRequestSchema.parse(params.payload)

  const response = await fetch(api(`/api/guilds/${params.guildId}/events`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(validated),
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || 'Failed to create event')
  }
  return data
}

async function cancelEvent(guildId: string, eventId: number) {
  const response = await fetch(api(`/api/guilds/${guildId}/events/${eventId}/cancel`), {
    method: 'POST',
    credentials: 'include',
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || 'Failed to cancel event')
  }
  return data
}

export function useEvents(guildId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['events', guildId],
    queryFn: () => fetchEvents(guildId!),
    enabled: enabled && !!guildId,
  })
}

export function useCreateEvent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ guildId, payload }: { guildId: string; payload: EventCreateRequest }) =>
      createEvent({ guildId, payload }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['events', variables.guildId] })
    },
  })
}

export function useCancelEvent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ guildId, eventId }: { guildId: string; eventId: number }) => 
      cancelEvent(guildId, eventId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['events', variables.guildId] })
    },
  })
}
