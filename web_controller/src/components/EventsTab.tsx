import React, { useState, useMemo } from 'react'
import { useGuilds, useUserPermissions } from '../hooks/useGuilds'
import { useEvents, useCreateEvent, useCancelEvent } from '../hooks/useEvents'
import { useAuth } from '../contexts/auth'
import { UpcomingEventsList } from './UpcomingEventsList'
import { CreateEventForm } from './CreateEventsForm'
import { GuildSelector } from './GuildSelector'

export const EventsTab: React.FC = () => {
  const { user } = useAuth()
  const { data: guilds } = useGuilds(!!user)
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null)
  const { data: userPermissions } = useUserPermissions(selectedGuildId)

  const { data: events, isLoading: eventsLoading, refetch } = useEvents(selectedGuildId, !!selectedGuildId)
  const createEvent = useCreateEvent()
  const cancelEvent = useCancelEvent()
  const guildOptions = useMemo(() => guilds ?? [], [guilds])

  React.useEffect(() => {
    if (!selectedGuildId && guildOptions.length > 0) {
      setSelectedGuildId(guildOptions[0].id)
    }
  }, [guildOptions, selectedGuildId])

  const sortedEvents = useMemo(() => {
    if (!events) return []
    return [...events].sort((a, b) => new Date(a.time_of_event).getTime() - new Date(b.time_of_event).getTime())
  }, [events])

  const canMakeEvents = userPermissions?.permissions?.make_events || false

  return (
    <div className="events-tab">
      <GuildSelector
        selectedGuildId={selectedGuildId}
        onGuildChange={setSelectedGuildId}
        guilds={guildOptions}
        label="Guild:"
      />

      <div className="events-layout">
        <div className="events-single-box">
          <div className="events-columns-inner">
            <div className="events-column">
              {canMakeEvents && (
                <CreateEventForm
                  selectedGuildId={selectedGuildId || ""}
                  createEvent={createEvent}
                  refetch={refetch}
                />
              )}
              {!canMakeEvents && selectedGuildId && (
                <div className="permission-warning">
                  <p>You don't have permission to create events in this server.</p>
                </div>
              )}
            </div>

            <div className="events-column">
              <UpcomingEventsList
                eventsLoading={eventsLoading}
                sortedEvents={sortedEvents}
                selectedGuildId={selectedGuildId}
                cancelEvent={cancelEvent}
                refetch={refetch}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EventsTab
