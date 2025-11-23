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
  permissions: z.union([z.string(), z.number()]).optional(),
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



export const SendMessageRequestSchema = z.object({
  guild_id: z.string(),
  channel_id: z.string(),
  message: z.string().min(1),
})

export type SendMessageRequest = z.infer<typeof SendMessageRequestSchema>

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

export const PermissionSchema = z.object({
  permission_name: z.union([
    z.literal('change_nickname'),
    z.literal('change_personality'),
    z.literal('make_events'),
    z.literal('manage_proposals'),
    z.string(),
  ]),
  allowed: z.boolean(),
})

export type Permission = z.infer<typeof PermissionSchema>

export const RoleSchema = z.object({
  role_id: z.string().optional(),
  role_name: z.string(),
  permissions: z.array(PermissionSchema),
})

export type Role = z.infer<typeof RoleSchema>

export const BotSettingsSchema = z.object({
  personality: z.string().optional(),
  bot_nickname: z.string().max(32).optional(),
})

export type BotSettings = z.infer<typeof BotSettingsSchema>

export const RoleSettingsSchema = z.object({
  roles: z.array(RoleSchema).optional(),
})

export type RoleSettings = z.infer<typeof RoleSettingsSchema>

export const ContentMaturityPreferencesSchema = z.object({
  banned_content: z.array(z.string()).optional(),
  allowed_maturity_score: z.number().min(0).max(10).optional(),
})

export type ContentMaturityPreferences = z.infer<typeof ContentMaturityPreferencesSchema>

export const GuildSettingsSchema = z.object({
  guild_id: z.string(),
  settings: z.object({
    bot_settings: BotSettingsSchema.optional(),
    role_settings: RoleSettingsSchema.optional(),
    content_maturity_preferences: ContentMaturityPreferencesSchema.optional(),
  }),
  edited_at: z.string().nullable(),
})

export type GuildSettings = z.infer<typeof GuildSettingsSchema>

export const UpdateGuildSettingsRequestSchema = z.object({
  settings: z.object({
    bot_settings: BotSettingsSchema.optional(),
    role_settings: RoleSettingsSchema.optional(),
    content_maturity_preferences: ContentMaturityPreferencesSchema.optional(),
  }),
})

export type UpdateGuildSettingsRequest = z.infer<typeof UpdateGuildSettingsRequestSchema>

export const OffenseSchema = z.object({
  offense_id: z.number(),
  guild_id: z.string(),
  channel_id: z.string(),
  user_id: z.string().nullable(),
  body: z.string().nullable(),
  picture: z.string().nullable().optional(),
  time_of_offense: z.string().optional(),
  offensive_score: z.number().nullable().optional(),
})

export type Offense = z.infer<typeof OffenseSchema>