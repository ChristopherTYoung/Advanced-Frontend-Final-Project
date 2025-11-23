type MaturitySettingsProps = {
  bannedContent: string[]
  setBannedContent: (content: string[]) => void
  allowedMaturityScore: number
  setAllowedMaturityScore: (score: number) => void
  isGuildOwner: boolean
}

export function MaturitySettings({
  bannedContent,
  setBannedContent,
  allowedMaturityScore,
  setAllowedMaturityScore,
  isGuildOwner
}: MaturitySettingsProps) {
  const handleAddBannedContent = () => {
    setBannedContent([...bannedContent, ''])
  }

  const handleRemoveBannedContent = (index: number) => {
    setBannedContent(bannedContent.filter((_, i) => i !== index))
  }

  const handleUpdateBannedContent = (index: number, value: string) => {
    const updated = [...bannedContent]
    updated[index] = value
    setBannedContent(updated)
  }

  return (
    <div className="maturity-settings">
      <h3>Content Maturity Preferences</h3>
      {!isGuildOwner && (
        <p className="permission-notice">Only the guild owner can modify maturity settings.</p>
      )}
      
      <div className="form-group">
        <label htmlFor="maturity-score">Allowed Maturity Score (0-10):</label>
        <input
          type="number"
          id="maturity-score"
          min="0"
          max="10"
          value={allowedMaturityScore}
          onChange={(e) => setAllowedMaturityScore(Number(e.target.value))}
          disabled={!isGuildOwner}
          style={{ opacity: isGuildOwner ? 1 : 0.6 }}
        />
        <small>Higher scores allow more mature content. 0 = all ages, 10 = mature content allowed</small>
      </div>

      <div className="form-group">
        <label>Banned Content Keywords:</label>
        {bannedContent.map((content, index) => (
          <div key={index} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <input
              type="text"
              value={content}
              onChange={(e) => handleUpdateBannedContent(index, e.target.value)}
              placeholder="Enter banned keyword or phrase"
              disabled={!isGuildOwner}
              style={{ flex: 1, opacity: isGuildOwner ? 1 : 0.6 }}
            />
            <button
              type="button"
              onClick={() => handleRemoveBannedContent(index)}
              disabled={!isGuildOwner}
              style={{ opacity: isGuildOwner ? 1 : 0.6 }}
            >
              Remove
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={handleAddBannedContent}
          disabled={!isGuildOwner}
          style={{ marginTop: '0.5rem', opacity: isGuildOwner ? 1 : 0.6 }}
        >
          Add Banned Content
        </button>
      </div>
    </div>
  )
}
