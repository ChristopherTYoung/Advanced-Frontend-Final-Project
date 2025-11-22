
type BotSettingsProps = {
    nickname: string;
    setNickname: (value: React.SetStateAction<string>) => void;
    canChangeNickname: boolean;
    personality: string;
    setPersonality: (value: React.SetStateAction<string>) => void;
    canChangePersonality: boolean;
}

export function BotSettings({ nickname,
    setNickname,
    canChangeNickname,
    personality,
    setPersonality,
    canChangePersonality }: BotSettingsProps) {
    return (
        <>
            <div className="form-group">
                <label htmlFor="nickname">Bot Nickname:</label>
                <input
                    id="nickname"
                    type="text"
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    placeholder="Enter bot nickname (max 32 characters)"
                    maxLength={32}
                    disabled={!canChangeNickname}
                    style={{ opacity: canChangeNickname ? 1 : 0.6, cursor: canChangeNickname ? 'text' : 'not-allowed' }}
                />
                <small>Leave empty to use default bot username {!canChangeNickname && '(You don\'t have permission to change this)'}</small>
            </div>

            <div className="form-group">
                <label htmlFor="personality">Bot Personality:</label>
                <textarea
                    id="personality"
                    value={personality}
                    onChange={(e) => setPersonality(e.target.value)}
                    placeholder="Enter bot personality description..."
                    rows={6}
                    disabled={!canChangePersonality}
                    style={{ opacity: canChangePersonality ? 1 : 0.6, cursor: canChangePersonality ? 'text' : 'not-allowed' }}
                />
                <small>
                    Example: "You are a friendly and helpful assistant. You love to make jokes and use emojis."
                    {!canChangePersonality && ' (You don\'t have permission to change this)'}
                </small>
            </div>
        </>
    )
}