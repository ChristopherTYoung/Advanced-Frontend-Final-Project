import type { QueryObserverResult, RefetchOptions, UseMutationResult } from '@tanstack/react-query';
import type { Event, EventProposal, ProposalMutationProps } from '../schemas/index';

type EventListProps = {
  proposalsLoading: boolean,
  pendingProposals: EventProposal[],
  selectedGuildId: string | null,
  approveProposal: UseMutationResult<any, Error, ProposalMutationProps, unknown>,
  refetchProposals: (options?: RefetchOptions | undefined) => Promise<QueryObserverResult<EventProposal[], Error>>,
  refetch: (options?: RefetchOptions | undefined) => Promise<QueryObserverResult<Event[], Error>>,
  deleteProposalMutation: UseMutationResult<any, Error, ProposalMutationProps, unknown>,
  approvedProposals: EventProposal[],
  canManageProposals: boolean
}

export function EventProposalList({ proposalsLoading,
  pendingProposals,
  selectedGuildId,
  approveProposal,
  refetchProposals,
  refetch,
  deleteProposalMutation,
  approvedProposals,
  canManageProposals }: EventListProps
) {
  return <div style={{ flex: 1 }}>
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
              {canManageProposals && (
                <div style={{ marginTop: 6 }}>
                  <button
                    onClick={async () => {
                      if (!selectedGuildId) return;
                      try {
                        await approveProposal.mutateAsync({ guildId: selectedGuildId, proposalId: p.proposal_id });
                        refetchProposals();
                        refetch();
                      } catch (err: any) {
                        console.error('Approve failed', err);
                      }
                    }}
                    disabled={Boolean((approveProposal as any).isLoading)}
                  >Approve</button>
                  <button
                    onClick={async () => {
                      if (!selectedGuildId) return;
                      try {
                        await deleteProposalMutation.mutateAsync({ guildId: selectedGuildId, proposalId: p.proposal_id });
                        refetchProposals();
                      } catch (err) {
                        console.error('Delete failed', err);
                      }
                    }}
                    style={{ marginLeft: 8 }}
                    disabled={Boolean((deleteProposalMutation as any).isLoading)}
                  >Reject</button>
                </div>
              )}
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
  </div>;
}
