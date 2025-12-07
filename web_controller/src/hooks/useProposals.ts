import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ProposalSchema, type Proposal } from '../schemas'
import { api } from '../utils/api'

async function fetchProposals(guildId: string): Promise<Proposal[]> {
  const response = await fetch(api(`/api/guilds/${guildId}/proposals`), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch proposals')
  }
  const data = await response.json()
  const arr = data.proposals || []
  const byId: Record<number, Proposal> = {}
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
    mutationFn: ({ guildId, proposalId }: { guildId: string; proposalId: number }) => 
      approveProposal(guildId, proposalId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['proposals', variables.guildId] })
      queryClient.invalidateQueries({ queryKey: ['events', variables.guildId] })
    },
  })
}

export function useDeleteProposal() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ guildId, proposalId }: { guildId: string; proposalId: number }) => 
      deleteProposal(guildId, proposalId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['proposals', variables.guildId] })
    },
  })
}
