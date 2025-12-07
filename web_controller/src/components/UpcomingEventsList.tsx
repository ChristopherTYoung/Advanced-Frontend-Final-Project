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
  return (
    <div className="upcoming-events-container">
      <h3>Upcoming Events</h3>
      {eventsLoading ? (
        <div className="loading-message">Loading...</div>
      ) : (
        <ul className="events-list">
          {sortedEvents.length === 0 && <li className="empty-message">No events</li>}
          {sortedEvents.map((ev) => (
            <li key={ev.event_id} className={`event-item ${ev.canceled ? 'canceled' : ''}`}>
              <div className="event-header">
                <strong>{ev.event_name}</strong>
                <span className="event-time">{new Date(ev.time_of_event).toLocaleString()}</span>
              </div>
              <div className="event-details">{ev.event_details}</div>
              {ev.canceled ? (
                <div className="canceled-info">Canceled: {new Date(ev.canceled).toLocaleString()}</div>
              ) : (
                <div className="event-actions">
                  <button
                    className="cancel-button"
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
                  >
                    Cancel
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
