import React, { useState, useMemo } from 'react'
import { useGuilds, useUserPermissions } from '../hooks/useGuilds'
import { useProposals, useApproveProposal, useDeleteProposal } from '../hooks/useProposals'
import { useAuth } from '../auth'
import { EventProposalList } from './EventProposalList'

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
      <div className="form-group">
        <label htmlFor="guild-select">Guild: </label>
        <select
          id="guild-select"
          value={selectedGuildId ?? ''}
          onChange={(e) => setSelectedGuildId(e.target.value || null)}
        >
          {guildOptions.map((g) => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
      </div>

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
  )
}

export default ProposalsTab
