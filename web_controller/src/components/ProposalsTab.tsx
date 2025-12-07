import React, { useState, useMemo } from 'react'
import { useGuilds, useUserPermissions } from '../hooks/useGuilds'
import { useProposals, useApproveProposal, useDeleteProposal } from '../hooks/useProposals'
import { useAuth } from '../contexts/auth'
import { EventProposalList } from './EventProposalList'
import { GuildSelector } from './GuildSelector'

export const ProposalsTab: React.FC = () => {
  const { user } = useAuth()
  const { data: guilds } = useGuilds(!!user)
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null)
  const { data: userPermissions } = useUserPermissions(selectedGuildId)

  const { data: proposals, isLoading: proposalsLoading, refetch: refetchProposals } = useProposals(selectedGuildId, !!selectedGuildId)
  const approveProposal = useApproveProposal()
  const deleteProposalMutation = useDeleteProposal()
  const guildOptions = useMemo(() => guilds ?? [], [guilds])

  React.useEffect(() => {
    if (!selectedGuildId && guildOptions.length > 0) {
      setSelectedGuildId(guildOptions[0].id)
    }
  }, [guildOptions, selectedGuildId])

  const pendingProposals = useMemo(() => {
    if (!proposals) return []
    return [...proposals].filter(p => !p.approved).sort((a, b) => new Date(a.time_of_event).getTime() - new Date(b.time_of_event).getTime())
  }, [proposals])

  const approvedProposals = useMemo(() => {
    if (!proposals) return []
    return [...proposals].filter(p => p.approved).sort((a, b) => new Date(a.time_of_event).getTime() - new Date(b.time_of_event).getTime())
  }, [proposals])

  const canManageProposals = userPermissions?.permissions?.manage_proposals || false

  return (
    <div className="proposals-tab">
      <div className="proposals-content">
        <GuildSelector
          selectedGuildId={selectedGuildId}
          onGuildChange={setSelectedGuildId}
          guilds={guildOptions}
          label="Guild:"
        />

        <EventProposalList
        proposalsLoading={proposalsLoading}
        pendingProposals={pendingProposals}
        selectedGuildId={selectedGuildId}
        approveProposal={approveProposal}
        refetchProposals={refetchProposals}
        deleteProposalMutation={deleteProposalMutation}
        approvedProposals={approvedProposals}
        canManageProposals={canManageProposals}
      />
      </div>
    </div>
  )
}

export default ProposalsTab
