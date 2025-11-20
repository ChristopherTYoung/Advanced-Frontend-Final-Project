DROP TABLE IF EXISTS message CASCADE;
DROP TABLE IF EXISTS event CASCADE;
DROP TABLE IF EXISTS guild_bot_settings CASCADE;

-- Create Guild Bot Settings table
CREATE TABLE guild_bot_settings (
    guild_id VARCHAR(100) PRIMARY KEY,
    bot_settings JSON,
    role_settings JSON,
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

-- Create Event table
CREATE TABLE event (
    event_id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    guild_id VARCHAR(100) NOT NULL,
    time_of_event TIMESTAMP NOT NULL,
    event_name VARCHAR(50) NOT NULL,
    event_details VARCHAR(200) NOT NULL,
    canceled TIMESTAMP DEFAULT(null)
);

CREATE INDEX idx_event_guild_id ON event(guild_id);
CREATE INDEX idx_event_user_id ON event(user_id);

CREATE TABLE event_proposal (
    proposal_id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    guild_id VARCHAR(100) NOT NULL,
    time_of_event TIMESTAMP NOT NULL,
    event_name VARCHAR(50) NOT NULL,
    event_details VARCHAR(200) NOT NULL,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    time_approved TIMESTAMP NULL,
    event_id INTEGER NULL REFERENCES event(event_id)
);

CREATE INDEX idx_event_proposal_guild_id ON event_proposal(guild_id);
CREATE INDEX idx_event_proposal_user_id ON event_proposal(user_id);