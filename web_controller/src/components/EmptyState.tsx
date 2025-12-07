interface EmptyStateProps {
  message: string
  hint?: string
}

export function EmptyState({ message, hint }: EmptyStateProps) {
  return (
    <div className="no-messages">
      <p>{message}</p>
      {hint && <p className="hint">{hint}</p>}
    </div>
  )
}
