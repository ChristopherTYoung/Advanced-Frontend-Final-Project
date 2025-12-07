-- Migration script to add username column to event and offense tables
ALTER TABLE event ADD COLUMN IF NOT EXISTS username VARCHAR(100);
ALTER TABLE offense ADD COLUMN IF NOT EXISTS username VARCHAR(100);

-- Optionally set a placeholder for existing records that don't have a username
UPDATE event SET username = 'Unknown User' WHERE username IS NULL;
UPDATE offense SET username = 'Unknown User' WHERE username IS NULL;
