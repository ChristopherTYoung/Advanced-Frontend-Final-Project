import { z } from 'zod'

// User schema
export const UserSchema = z.object({
  id: z.string(),
  username: z.string(),
  avatar: z.string(),
  discriminator: z.string(),
  email: z.string().email().optional(),
})

export type User = z.infer<typeof UserSchema>

// Guild schema
export const GuildSchema = z.object({
  id: z.string(),
  name: z.string(),
  icon: z.string().nullable(),
  owner: z.boolean().optional(),
  permissions: z.string().optional(),
})

export type Guild = z.infer<typeof GuildSchema>

// Channel schema
export const ChannelSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.number(),
})

export type Channel = z.infer<typeof ChannelSchema>

// Message schema
export const MessageSchema = z.object({
  id: z.string(),
  type: z.string(),
  content: z.string(),
  timestamp: z.string(),
  user_id: z.string(),
  username: z.string(),
  guild_id: z.string().optional(),
  guild_name: z.string().optional(),
  channel_id: z.string().optional(),
  channel_name: z.string().optional(),
})

export type Message = z.infer<typeof MessageSchema>

// Guild settings schema
export const GuildSettingsSchema = z.object({
  guild_id: z.string(),
  settings: z.object({
    personality: z.string().optional(),
    bot_nickname: z.string().max(32).optional(),
  }),
  edited_at: z.string().nullable(),
})

export type GuildSettings = z.infer<typeof GuildSettingsSchema>

// Request schemas
export const SendMessageRequestSchema = z.object({
  guild_id: z.string(),
  channel_id: z.string(),
  message: z.string().min(1),
})

export type SendMessageRequest = z.infer<typeof SendMessageRequestSchema>

export const UpdateGuildSettingsRequestSchema = z.object({
  settings: z.object({
    personality: z.string().optional(),
    bot_nickname: z.string().max(32).optional(),
  }),
})

export type UpdateGuildSettingsRequest = z.infer<typeof UpdateGuildSettingsRequestSchema>

// Response schemas
export const ApiErrorSchema = z.object({
  error: z.string(),
  detail: z.string().optional(),
})

export type ApiError = z.infer<typeof ApiErrorSchema>

export const SuccessResponseSchema = z.object({
  message: z.string(),
})

export type SuccessResponse = z.infer<typeof SuccessResponseSchema>
