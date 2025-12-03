import type { QueryObserverResult, RefetchOptions, UseMutationResult } from '@tanstack/react-query';
import type { Event } from "../schemas/index"

type EventMutationProps = {
  guildId: string;
  eventId: number;
}
type UpcomingEventsProps = {
  eventsLoading: boolean, 
  sortedEvents: Event[], 
  selectedGuildId: string | null, 
  cancelEvent: UseMutationResult<unknown, Error, EventMutationProps, unknown>, 
  refetch: (options?: RefetchOptions | undefined) => Promise<QueryObserverResult<Event[], Error>>
}
export function UpcomingEventsList({ eventsLoading, sortedEvents, selectedGuildId, cancelEvent, refetch}: UpcomingEventsProps) {
  return <div style={{ flex: 1 }}>
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
                    if (!selectedGuildId) return;
                    try {
                      await cancelEvent.mutateAsync({ guildId: selectedGuildId, eventId: ev.event_id });
                      refetch();
                    } catch (err) {
                      console.error('Cancel failed', err);
                    }
                  }}
                  disabled={cancelEvent.isPending}
                >Cancel</button>
              </div>
            )}
          </li>
        ))}
      </ul>
    )}
  </div>;
}
