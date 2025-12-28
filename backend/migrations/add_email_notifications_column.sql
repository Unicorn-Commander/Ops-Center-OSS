-- Epic 2.3: Email Notifications System
-- Migration: Add email_notifications_enabled column to user_credits table
-- Date: October 24, 2025

-- Add email_notifications_enabled column (default TRUE)
ALTER TABLE user_credits
ADD COLUMN IF NOT EXISTS email_notifications_enabled BOOLEAN DEFAULT TRUE;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_credits_email_enabled
ON user_credits(email_notifications_enabled);

-- Add comment
COMMENT ON COLUMN user_credits.email_notifications_enabled IS
'Whether user has email notifications enabled (TRUE by default)';

-- Set all existing users to enabled
UPDATE user_credits
SET email_notifications_enabled = TRUE
WHERE email_notifications_enabled IS NULL;
