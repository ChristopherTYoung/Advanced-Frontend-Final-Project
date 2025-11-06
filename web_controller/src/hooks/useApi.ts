import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

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

// Types
interface User {
  id: string
  username: string
  avatar: string
  discriminator: string
}

interface Guild {
  id: string
  name: string
  icon: string | null
  owner: boolean
  permissions: string
}

interface Channel {
  id: string
  name: string
  type: number
}

interface Message {
  id: string
  type: string
  content: string
  timestamp: string
  user_id: string
  username: string
  guild_id?: string
  guild_name?: string
  channel_id?: string
  channel_name?: string
}

// API Functions
async function fetchUser(): Promise<User | null> {
  const response = await fetch(api('/api/me'), {
    credentials: 'include'
  })
  if (!response.ok) return null
  const data = await response.json()
  return data.user
}

async function fetchGuilds(): Promise<Guild[]> {
  const response = await fetch(api('/api/guilds'), {
    credentials: 'include'
  })
  if (!response.ok) throw new Error('Failed to fetch guilds')
  const data = await response.json()
  return data.guilds || []
}

async function fetchChannels(guildId: string): Promise<Channel[]> {
  const response = await fetch(api(`/api/guilds/${guildId}/channels`), {
    credentials: 'include'
  })
  if (!response.ok) throw new Error('Failed to fetch channels')
  const data = await response.json()
  return data.channels || []
}

async function fetchMessages(messageType: string = 'received'): Promise<Message[]> {
  const response = await fetch(api(`/api/messages?message_type=${messageType}`), {
    credentials: 'include'
  })
  if (!response.ok) throw new Error('Failed to fetch messages')
  const data = await response.json()
  return data.messages || []
}

async function sendMessage(params: {
  guildId: string
  channelId: string
  message: string
  userId?: string
  username?: string
}): Promise<{ success: boolean; message: string }> {
  const response = await fetch(api('/api/send-message'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({
      guild_id: params.guildId,
      channel_id: params.channelId,
      message: params.message,
      user_id: params.userId,
      username: params.username
    })
  })
  
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error || 'Failed to send message')
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

export function useMessages(messageType: string = 'received', enabled: boolean = true) {
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

// Export api helper for other uses
export { api }
