-- Migration script to add username column to message table
ALTER TABLE message ADD COLUMN IF NOT EXISTS username VARCHAR(100);

-- Optionally set a placeholder for existing records that don't have a username
UPDATE message SET username = 'Unknown User' WHERE username IS NULL;
