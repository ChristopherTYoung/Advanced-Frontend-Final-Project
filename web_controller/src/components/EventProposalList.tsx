import type { QueryObserverResult, RefetchOptions, UseMutationResult } from '@tanstack/react-query';
import type { EventProposal, ProposalMutationProps } from '../schemas/index';

type EventListProps = {
  proposalsLoading: boolean,
  pendingProposals: EventProposal[],
  selectedGuildId: string | null,
  approveProposal: UseMutationResult<unknown, Error, ProposalMutationProps, unknown>,
  refetchProposals: (options?: RefetchOptions | undefined) => Promise<QueryObserverResult<EventProposal[], Error>>,
  deleteProposalMutation: UseMutationResult<unknown, Error, ProposalMutationProps, unknown>,
  approvedProposals: EventProposal[],
  canManageProposals: boolean
}

export function EventProposalList({ proposalsLoading,
  pendingProposals,
  selectedGuildId,
  approveProposal,
  refetchProposals,
  deleteProposalMutation,
  approvedProposals,
  canManageProposals }: EventListProps
) {
  return (
    <div className="proposals-container">
      {proposalsLoading ? (
        <div className="loading-message">Loading proposals...</div>
      ) : (
        <div className="proposals-columns">
          <div className="proposal-section">
            <h4>Pending</h4>
            <ul className="proposal-list">
              {pendingProposals.length === 0 && <li className="empty-message">No pending proposals</li>}
              {pendingProposals.map((p) => (
                <li key={p.proposal_id} className="proposal-item">
                  <div className="proposal-header">
                    <strong>{p.event_name}</strong>
                    <span className="proposal-time">{new Date(p.time_of_event).toLocaleString()}</span>
                  </div>
                  <div className="proposal-details">{p.event_details}</div>
                  <div className="proposal-meta">Proposed by: {p.username || p.user_id || 'Unknown User'}</div>
                  {canManageProposals && (
                    <div className="proposal-actions">
                      <button
                        className="approve-button"
                        onClick={async () => {
                          if (!selectedGuildId) return;
                          try {
                            await approveProposal.mutateAsync({ guildId: selectedGuildId, proposalId: p.proposal_id });
                            refetchProposals();
                          } catch (err) {
                            console.error('Approve failed', err);
                          }
                        }}
                        disabled={approveProposal.isPending}
                      >
                        Approve
                      </button>
                      <button
                        className="reject-button"
                        onClick={async () => {
                          if (!selectedGuildId) return;
                          try {
                            await deleteProposalMutation.mutateAsync({ guildId: selectedGuildId, proposalId: p.proposal_id });
                            refetchProposals();
                          } catch (err) {
                            console.error('Delete failed', err);
                          }
                        }}
                        disabled={deleteProposalMutation.isPending}
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>

          <div className="proposal-section">
            <h4>Approved</h4>
            <ul className="proposal-list">
              {approvedProposals.length === 0 && <li className="empty-message">No approved proposals</li>}
              {approvedProposals.map((p) => (
                <li key={p.proposal_id} className="proposal-item approved">
                  <div className="proposal-header">
                    <strong>{p.event_name}</strong>
                    <span className="proposal-time">{new Date(p.time_of_event).toLocaleString()}</span>
                  </div>
                  <div className="proposal-details">{p.event_details}</div>
                  <div className="proposal-meta">Proposed by: {p.username || p.user_id || 'Unknown User'}</div>
                  <div className="approval-info">
                    Approved at: {p.time_approved ? new Date(p.time_approved).toLocaleString() : '—'}
                    {p.event_id ? ` — event id ${p.event_id}` : ''}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
