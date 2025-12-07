interface SetupTabProps {
  botInviteUrl: string
}

export function SetupTab({ botInviteUrl }: SetupTabProps) {
  return (
    <div className="setup-page">
      <div className="setup-card">
        <div className="setup-steps">
          <div className="step">
            <h3>Step 1: Invite the Bot</h3>
            <p>Click the button below to add the bot to a server you own or manage.</p>
            {botInviteUrl ? (
              <a 
                href={botInviteUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="invite-btn"
              >
                Add Bot to Server
              </a>
            ) : (
              <p className="error">Bot client ID not configured</p>
            )}
          </div>

          <div className="step">
            <h3>Step 2: Select Server</h3>
            <p>Choose the server where you want to add the bot from the Discord authorization page.</p>
          </div>

          <div className="step">
            <h3>Step 3: Authorize Permissions</h3>
            <p>Review and authorize the requested permissions for the bot to function properly.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
