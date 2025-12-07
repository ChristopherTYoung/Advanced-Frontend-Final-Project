import { useState } from "react"
import type { EventCreateRequest, Event as SchemaEvent } from "../schemas";
import type { QueryObserverResult, RefetchOptions, UseMutationResult } from "@tanstack/react-query";
import { useAuth } from "../contexts/auth";
type CreateEventFormProps = {
    selectedGuildId: string;
    createEvent: UseMutationResult<unknown, Error, { guildId: string; payload: EventCreateRequest; }, unknown>,
    refetch: (options?: RefetchOptions | undefined) => Promise<QueryObserverResult<SchemaEvent[], Error>>
}
export function CreateEventForm({ selectedGuildId, createEvent, refetch }: CreateEventFormProps) {
    const { user } = useAuth()
    const [eventName, setEventName] = useState('')
    const [eventDetails, setEventDetails] = useState('')
    const [timeLocal, setTimeLocal] = useState('')
    const [error, setError] = useState<string | null>(null)

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
            await refetch()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create event')
        }
    }
    return (
        <div className="event-form-container">
            <h3>Create Event</h3>
            <form onSubmit={handleSubmit}>
                <div className="form-field">
                    <label>Event name</label>
                    <input value={eventName} onChange={(e) => setEventName(e.target.value)} />
                </div>

                <div className="form-field">
                    <label>Details</label>
                    <textarea value={eventDetails} onChange={(e) => setEventDetails(e.target.value)} rows={4} />
                </div>

                <div className="form-field">
                    <label>Time</label>
                    <input
                        type="datetime-local"
                        value={timeLocal}
                        onChange={(e) => setTimeLocal(e.target.value)}
                    />
                </div>

                <div className="form-actions">
                    <button type="submit" className="submit-button" disabled={createEvent.isPending || !user}>Add Event</button>
                    {!user && <div className="info-message">Sign in to create events</div>}
                </div>

                {error && <div className="error-message">{error}</div>}
                {createEvent.error && <div className="error-message">{createEvent.error.message}</div>}
            </form>
        </div>
    )
}