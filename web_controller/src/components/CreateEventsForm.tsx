import { useState } from "react"
import type { EventCreateRequest, User, Event as SchemaEvent } from "../schemas";
import type { QueryObserverResult, RefetchOptions, UseMutationResult } from "@tanstack/react-query";
import { useAuth } from "../auth";
type CreateEventFormProps = {
    selectedGuildId: string;
    createEvent: UseMutationResult<any, Error, { guildId: string; payload: EventCreateRequest; }, unknown>,
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
        } catch (err: any) {
            setError(err?.message || 'Failed to create event')
        }
    }
    return (
        <>
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
                            <button type="submit" disabled={Boolean((createEvent as any).isLoading) || !user}>Add Event</button>
                            {!user && <div style={{ color: '#666', fontSize: 12, marginTop: 6 }}>Sign in to create events</div>}
                        </div>

                        {error && <div style={{ color: 'red', marginTop: 8 }}>{error}</div>}
                        {createEvent.error && <div style={{ color: 'red', marginTop: 8 }}>{(createEvent.error as any).message}</div>}
                    </form>
                </div>
            </div>
        </>
    )
}