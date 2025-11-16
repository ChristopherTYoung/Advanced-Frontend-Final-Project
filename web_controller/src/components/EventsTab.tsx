import React, { useState, useMemo } from 'react'
import { useGuilds } from '../hooks/useApi'
import { useEvents, useCreateEvent, useProposals, useApproveProposal, useDeleteProposal, useCancelEvent } from '../hooks/useApi'
import { useAuth } from '../auth'

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

  const [eventName, setEventName] = useState('')
  const [eventDetails, setEventDetails] = useState('')
  const [timeLocal, setTimeLocal] = useState('')
  const [error, setError] = useState<string | null>(null)

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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!selectedGuildId) return setError('No guild selected')
    if (!user || !user.id) return setError('Not authenticated')
    if (!eventName.trim()) return setError('Event name required')
    if (!timeLocal) return setError('Event time required')

    const dt = new Date(timeLocal)
    if (isNaN(dt.getTime())) return setError('Invalid date/time')
    const iso = dt.toISOString()

    try {
      await createEvent.mutateAsync({
        guildId: selectedGuildId,
        payload: {
          user_id: user.id,
          time_of_event: iso,
          event_name: eventName.trim(),
          event_details: eventDetails.trim(),
        },
      })

      setEventName('')
      setEventDetails('')
      setTimeLocal('')
      refetch()
    } catch (err: any) {
      setError(err?.message || 'Failed to create event')
    }
  }

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

      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ flex: 1 }}>
          <h3>Create Event</h3>
          <form onSubmit={handleSubmit}>
            <div>
              <label>Event name</label>
              <br />
              <input value={eventName} onChange={(e) => setEventName(e.target.value)} />
            </div>

            <div>
              <label>Details</label>
              <br />
              <textarea value={eventDetails} onChange={(e) => setEventDetails(e.target.value)} rows={4} />
            </div>

            <div>
              <label>Time</label>
              <br />
              <input
                type="datetime-local"
                value={timeLocal}
                onChange={(e) => setTimeLocal(e.target.value)}
              />
            </div>

            <div style={{ marginTop: 8 }}>
              <button type="submit" disabled={Boolean((createEvent as any).isLoading)}>Add Event</button>
            </div>

            {error && <div style={{ color: 'red', marginTop: 8 }}>{error}</div>}
            {createEvent.error && <div style={{ color: 'red', marginTop: 8 }}>{(createEvent.error as any).message}</div>}
          </form>
        </div>

        <div style={{ flex: 1 }}>
          <h3>Upcoming Events</h3>
          {eventsLoading ? (
            <div>Loading...</div>
          ) : (
            <ul>
              {sortedEvents.length === 0 && <li>No events</li>}
              {sortedEvents.map((ev) => (
                <li key={ev.event_id}>
                  <strong>{ev.event_name}</strong> — {new Date(ev.time_of_event).toLocaleString()}
                  <div>{ev.event_details}</div>
                  {ev.canceled ? (
                    <div style={{ color: 'red', fontSize: 12 }}>Canceled: {new Date(ev.canceled).toLocaleString()}</div>
                  ) : (
                    <div style={{ marginTop: 6 }}>
                      <button
                        onClick={async () => {
                          if (!selectedGuildId) return
                          try {
                            await cancelEvent.mutateAsync({ guildId: selectedGuildId, eventId: ev.event_id })
                            refetch()
                          } catch (err) {
                            console.error('Cancel failed', err)
                          }
                        }}
                        disabled={Boolean((cancelEvent as any).isLoading)}
                      >Cancel</button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div style={{ flex: 1 }}>
          <h3>Event Proposals</h3>
          {proposalsLoading ? (
            <div>Loading proposals...</div>
          ) : (
            <>
              <h4>Pending</h4>
              <ul>
                {pendingProposals.length === 0 && <li>No pending proposals</li>}
                {pendingProposals.map((p) => (
                  <li key={p.proposal_id} style={{ marginBottom: 8 }}>
                    <strong>{p.event_name}</strong> — {new Date(p.time_of_event).toLocaleString()}
                    <div>{p.event_details}</div>
                    <div style={{ marginTop: 6 }}>
                      <button
                        onClick={async () => {
                          if (!selectedGuildId) return
                          try {
                            await approveProposal.mutateAsync({ guildId: selectedGuildId, proposalId: p.proposal_id })
                            refetchProposals()
                            refetch()
                          } catch (err: any) {
                            console.error('Approve failed', err)
                          }
                        }}
                        disabled={Boolean((approveProposal as any).isLoading)}
                      >Approve</button>
                      <button
                        onClick={async () => {
                          if (!selectedGuildId) return
                          try {
                            await deleteProposalMutation.mutateAsync({ guildId: selectedGuildId, proposalId: p.proposal_id })
                            refetchProposals()
                          } catch (err) {
                            console.error('Delete failed', err)
                          }
                        }}
                        style={{ marginLeft: 8 }}
                        disabled={Boolean((deleteProposalMutation as any).isLoading)}
                      >Reject</button>
                    </div>
                  </li>
                ))}
              </ul>

              <h4>Approved</h4>
              <ul>
                {approvedProposals.length === 0 && <li>No approved proposals</li>}
                {approvedProposals.map((p) => (
                  <li key={p.proposal_id}>
                    <strong>{p.event_name}</strong> — {new Date(p.time_of_event).toLocaleString()}
                    <div>{p.event_details}</div>
                    <div style={{ color: '#666', fontSize: 12 }}>
                      Approved at: {p.time_approved ? new Date(p.time_approved).toLocaleString() : '—'}
                      {p.event_id ? ` — event id ${p.event_id}` : ''}
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default EventsTab
