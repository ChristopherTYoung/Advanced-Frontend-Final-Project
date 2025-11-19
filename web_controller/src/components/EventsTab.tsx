import React, { useState, useMemo } from 'react'
import { useGuilds } from '../hooks/useApi'
import { useEvents, useCreateEvent, useProposals, useApproveProposal, useDeleteProposal, useCancelEvent } from '../hooks/useApi'
import { useAuth } from '../auth'
import { EventProposalList } from './EventsList'
import { UpcomingEventsList } from './UpcomingEventsList'
import { CreateEventForm } from './CreateEventsForm'

export const EventsTab: React.FC = () => {
  const { user } = useAuth()
  const { data: guilds } = useGuilds(!!user)
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null)

  const { data: events, isLoading: eventsLoading, refetch } = useEvents(selectedGuildId, !!selectedGuildId)
  const createEvent = useCreateEvent()
  const cancelEvent = useCancelEvent()
  const { data: proposals, isLoading: proposalsLoading, refetch: refetchProposals } = useProposals(selectedGuildId, !!selectedGuildId)
  const approveProposal = useApproveProposal()
  const deleteProposalMutation = useDeleteProposal()
  const guildOptions = guilds ?? []

  React.useEffect(() => {
    if (!selectedGuildId && guildOptions.length > 0) {
      setSelectedGuildId(guildOptions[0].id)
    }
  }, [guildOptions, selectedGuildId])

  const sortedEvents = useMemo(() => {
    if (!events) return []
    return [...events].sort((a, b) => new Date(a.time_of_event).getTime() - new Date(b.time_of_event).getTime())
  }, [events])

  const pendingProposals = useMemo(() => {
    if (!proposals) return []
    return [...proposals].filter(p => !p.approved).sort((a, b) => new Date(a.time_of_event).getTime() - new Date(b.time_of_event).getTime())
  }, [proposals])

  const approvedProposals = useMemo(() => {
    if (!proposals) return []
    return [...proposals].filter(p => p.approved).sort((a, b) => new Date(a.time_of_event).getTime() - new Date(b.time_of_event).getTime())
  }, [proposals])

  return (
    <div>
      <h2>Events</h2>

      <div style={{ marginBottom: 12 }}>
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
      <CreateEventForm
        selectedGuildId={selectedGuildId || ""}
        createEvent={createEvent}
        refetch={refetch}
      />

      <UpcomingEventsList
        eventsLoading={eventsLoading}
        sortedEvents={sortedEvents}
        selectedGuildId={selectedGuildId}
        cancelEvent={cancelEvent}
        refetch={refetch}
      />

      <EventProposalList
        proposalsLoading={proposalsLoading}
        pendingProposals={pendingProposals}
        selectedGuildId={selectedGuildId}
        approveProposal={approveProposal}
        refetchProposals={refetchProposals}
        refetch={refetch}
        deleteProposalMutation={deleteProposalMutation}
        approvedProposals={approvedProposals}
      />
    </div>
  )
}

export default EventsTab
