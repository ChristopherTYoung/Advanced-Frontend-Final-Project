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
  type User,
  type Guild,
  type Channel,
  type Message,
  type GuildSettings,
} from '../schemas'

const API_BASE_URL = import.meta.env.VITE_DISCORD_BOT_URL || window.ENV?.VITE_DISCORD_BOT_URL

function api(path: string): string {
  // In development with Vite dev server, use relative URLs so the proxy works
  // In production, use the full bot URL from env
  const isDev = import.meta.env.DEV
  
  if (isDev) {
    // Use relative URL - Vite proxy will forward to backend
    console.log('API Request (dev, proxied):', path)
    return path
  } else {
    // Use full URL in production
    const baseUrl = API_BASE_URL?.replace(/\/$/, '') || ''
    const fullUrl = `${baseUrl}${path}`
    console.log('API Request (prod):', fullUrl)
    return fullUrl
  }
}

// API Functions
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
  // Backend returns { guilds: [...] }, so extract the guilds array
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
  // Backend returns { channels: [...] }, so extract the channels array
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

// Export api helper for other uses
export { api }
