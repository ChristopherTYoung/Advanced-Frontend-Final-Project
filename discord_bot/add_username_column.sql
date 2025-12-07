-- Add username column to event_proposal table
ALTER TABLE event_proposal ADD COLUMN IF NOT EXISTS username VARCHAR(100);

-- Update existing rows to have a placeholder username
UPDATE event_proposal SET username = 'Unknown User' WHERE username IS NULL;
