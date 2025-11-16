import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import {
  UserSchema,
  GuildSchema,
  ChannelSchema,
  MessageSchema,
  GuildSettingsSchema,
  SendMessageRequestSchema,
  UpdateGuildSettingsRequestSchema,
  EventSchema,
  EventCreateRequestSchema,
  ProposalSchema,
  type User,
  type Guild,
  type Channel,
  type Message,
  type GuildSettings,
  type Event,
  type EventCreateRequest,
  type Proposal,
} from '../schemas'

const API_BASE_URL = import.meta.env.VITE_DISCORD_BOT_URL || window.ENV?.VITE_DISCORD_BOT_URL

function api(path: string): string {
  const isDev = import.meta.env.DEV
  
  if (isDev) {
    console.log('API Request (dev, proxied):', path)
    return path
  } else {
    const baseUrl = API_BASE_URL?.replace(/\/$/, '') || ''
    const fullUrl = `${baseUrl}${path}`
    console.log('API Request (prod):', fullUrl)
    return fullUrl
  }
}

async function fetchUser(): Promise<User> {
  const response = await fetch(api('/api/user'), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch user')
  }
  const data = await response.json()
  return UserSchema.parse(data)
}

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

async function fetchChannels(guildId: string): Promise<Channel[]> {
  const response = await fetch(api(`/api/guilds/${guildId}/channels`), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch channels')
  }
  const data = await response.json()
  const channelsArray = data.channels || []
  return z.array(ChannelSchema).parse(channelsArray)
}

async function fetchMessages(messageType?: string): Promise<Message[]> {
  const url = messageType ? `/api/messages?message_type=${messageType}` : '/api/messages'
  const response = await fetch(api(url), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch messages')
  }
  const data = await response.json()
  // Backend returns { messages: [...] }, so extract the messages array
  const messagesArray = data.messages || []
  return z.array(MessageSchema).parse(messagesArray)
}

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

async function sendMessage(params: { guildId: string; channelId: string; message: string }) {
  // Validate request data
  const validated = SendMessageRequestSchema.parse({
    guild_id: params.guildId,
    channel_id: params.channelId,
    message: params.message,
  })

  const response = await fetch(api(`/api/guilds/${params.guildId}/channels/${params.channelId}/messages`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(validated),
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || 'Failed to send message')
  }
  return data
}

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

async function updateGuildSettings(guildId: string, settings: { personality?: string, bot_nickname?: string }) {
  // Validate request data
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

// Hooks
export function useUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: fetchUser,
  })
}

export function useGuilds(enabled: boolean = true) {
  return useQuery({
    queryKey: ['guilds'],
    queryFn: fetchGuilds,
    enabled,
  })
}

export function useChannels(guildId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['channels', guildId],
    queryFn: () => fetchChannels(guildId!),
    enabled: enabled && !!guildId,
  })
}

export function useMessages(messageType?: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['messages', messageType],
    queryFn: () => fetchMessages(messageType),
    enabled,
  })
}

export function useEvents(guildId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['events', guildId],
    queryFn: () => fetchEvents(guildId!),
    enabled: enabled && !!guildId,
  })
}

async function fetchProposals(guildId: string): Promise<Proposal[]> {
  const response = await fetch(api(`/api/guilds/${guildId}/proposals`), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch proposals')
  }
  const data = await response.json()
  const arr = data.proposals || []
  const byId: Record<number, any> = {}
  for (const p of arr) {
    try {
      const parsed = ProposalSchema.parse(p)
      byId[parsed.proposal_id] = parsed
    } catch (e) {
      console.warn('Invalid proposal entry skipped', e)
    }
  }
  return Object.values(byId) as Proposal[]
}

async function approveProposal(guildId: string, proposalId: number) {
  const response = await fetch(api(`/api/guilds/${guildId}/proposals/${proposalId}/approve`), {
    method: 'POST',
    credentials: 'include',
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || 'Failed to approve proposal')
  }
  return data
}

async function deleteProposal(guildId: string, proposalId: number) {
  const response = await fetch(api(`/api/guilds/${guildId}/proposals/${proposalId}`), {
    method: 'DELETE',
    credentials: 'include',
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || 'Failed to delete proposal')
  }
  return data
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
    mutationFn: ({ guildId, eventId }: { guildId: string; eventId: number }) => cancelEvent(guildId, eventId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['events', variables.guildId] })
    },
  })
}

export function useProposals(guildId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['proposals', guildId],
    queryFn: () => fetchProposals(guildId!),
    enabled: enabled && !!guildId,
  })
}

export function useApproveProposal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ guildId, proposalId }: { guildId: string; proposalId: number }) => approveProposal(guildId, proposalId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['proposals', variables.guildId] })
      queryClient.invalidateQueries({ queryKey: ['events', variables.guildId] })
    },
  })
}

export function useDeleteProposal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ guildId, proposalId }: { guildId: string; proposalId: number }) => deleteProposal(guildId, proposalId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['proposals', variables.guildId] })
    },
  })
}

export function useSendMessage() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: sendMessage,
    onSuccess: () => {
      // Invalidate messages query to refetch
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
  })
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
    mutationFn: ({ guildId, settings }: { guildId: string, settings: { personality?: string, bot_nickname?: string } }) => 
      updateGuildSettings(guildId, settings),
    onSuccess: (_, variables) => {
      // Invalidate guild settings query to refetch
      queryClient.invalidateQueries({ queryKey: ['guildSettings', variables.guildId] })
    },
  })
}

export { api }
