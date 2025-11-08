DROP TABLE IF EXISTS message CASCADE;
DROP TABLE IF EXISTS guild_bot_settings CASCADE;

-- Create Guild Bot Settings table
CREATE TABLE guild_bot_settings (
    guild_id VARCHAR(100) PRIMARY KEY,
    settings JSON,
    edited_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create Message table
CREATE TABLE message (
    message_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(100),
    channel_id VARCHAR(100),
    user_id VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    body VARCHAR(2000) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_message_guild_id ON message(guild_id);
CREATE INDEX idx_message_channel_id ON message(channel_id);
CREATE INDEX idx_guild_bot_settings_guild_id ON guild_bot_settings(guild_id);
CREATE INDEX idx_message_role ON message(role);