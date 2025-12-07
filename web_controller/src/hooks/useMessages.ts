import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { MessageSchema, type Message } from '../schemas'
import { api } from '../utils/api'

async function fetchMessages(messageType?: string): Promise<Message[]> {
  const url = messageType ? `/api/messages?message_type=${messageType}` : '/api/messages'
  const response = await fetch(api(url), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch messages')
  }
  const data = await response.json()
  const messagesArray = data.messages || []
  return z.array(MessageSchema).parse(messagesArray)
}

export function useMessages(messageType?: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['messages', messageType],
    queryFn: () => fetchMessages(messageType),
    enabled,
  })
}
