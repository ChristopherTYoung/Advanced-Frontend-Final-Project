import { z } from 'zod'

export const UserSchema = z.object({
  id: z.string(),
  username: z.string(),
  avatar: z.string(),
  discriminator: z.string(),
  email: z.string().email().optional(),
})

export type User = z.infer<typeof UserSchema>

export const GuildSchema = z.object({
  id: z.string(),
  name: z.string(),
  icon: z.string().nullable(),
  owner: z.boolean().optional(),
  permissions: z.string().optional(),
})

export type Guild = z.infer<typeof GuildSchema>

export const ChannelSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.number(),
})

export type Channel = z.infer<typeof ChannelSchema>

export const MessageSchema = z.object({
  id: z.string(),
  type: z.string(),
  content: z.string(),
  timestamp: z.string(),
  user_id: z.string().nullable(),
  username: z.string().nullable(),
  guild_id: z.string().optional().nullable(),
  guild_name: z.string().optional().nullable(),
  channel_id: z.string().optional().nullable(),
  channel_name: z.string().optional().nullable(),
})

export type Message = z.infer<typeof MessageSchema>

export const GuildSettingsSchema = z.object({
  guild_id: z.string(),
  settings: z.object({
    personality: z.string().optional(),
    bot_nickname: z.string().max(32).optional(),
  }),
  edited_at: z.string().nullable(),
})

export type GuildSettings = z.infer<typeof GuildSettingsSchema>

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

export const ApiErrorSchema = z.object({
  error: z.string(),
  detail: z.string().optional(),
})

export type ApiError = z.infer<typeof ApiErrorSchema>

export const SuccessResponseSchema = z.object({
  message: z.string(),
})

export type SuccessResponse = z.infer<typeof SuccessResponseSchema>

export const EventSchema = z.object({
  event_id: z.number(),
  user_id: z.string(),
  guild_id: z.string(),
  time_of_event: z.string(),
  event_name: z.string(),
  event_details: z.string(),
  canceled: z.string().nullable().optional(),
})

export type Event = z.infer<typeof EventSchema>

export const EventCreateRequestSchema = z.object({
  user_id: z.string(),
  time_of_event: z.string(),
  event_name: z.string().min(1).max(50),
  event_details: z.string().max(200),
})

export type EventCreateRequest = z.infer<typeof EventCreateRequestSchema>

export const ProposalSchema = z.object({
  proposal_id: z.number(),
  user_id: z.string(),
  guild_id: z.string(),
  created_at: z.string(),
  time_of_event: z.string(),
  event_name: z.string(),
  event_details: z.string().optional(),
  approved: z.boolean(),
  time_approved: z.string().nullable(),
  event_id: z.number().nullable(),
})

export type Proposal = z.infer<typeof ProposalSchema>

export const EventProposalSchema = z.object({
  proposal_id: z.number(),
  user_id: z.string(),
  guild_id: z.string(),
  created_at: z.string(),
  time_of_event: z.string(),
  event_name: z.string(),
  approved: z.boolean(),
  time_approved: z.string().nullable(),
  event_id: z.number().nullable(),
  event_details: z.string().optional(),
})

export type EventProposal = z.infer<typeof EventProposalSchema>

export const ProposalCreateRequestSchema = z.object({
  user_id: z.string(),
  time_of_event: z.string(),
  event_name: z.string().min(1).max(50),
  event_details: z.string().max(500).optional(),
})

export type ProposalCreateRequest = z.infer<typeof ProposalCreateRequestSchema>

export const ProposalMutationPropsSchema = z.object({
  guildId: z.string(),
  proposalId: z.number(),
})

export type ProposalMutationProps = z.infer<typeof ProposalMutationPropsSchema>