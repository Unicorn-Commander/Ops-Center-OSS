-- Add launch URLs for apps that are missing them
-- Run with: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /path/to/this/file.sql

-- Update Unicorn Amanuensis (Speech-to-Text)
UPDATE add_ons
SET launch_url = 'https://stt.unicorncommander.ai'
WHERE name = 'Unicorn Amanuensis'
  AND (launch_url IS NULL OR launch_url = '');

-- Update Unicorn Orator (Text-to-Speech)
UPDATE add_ons
SET launch_url = 'https://tts.unicorncommander.ai'
WHERE name = 'Unicorn Orator'
  AND (launch_url IS NULL OR launch_url = '');

-- Verify all active apps now have launch URLs
SELECT
  name,
  launch_url,
  is_active,
  CASE
    WHEN launch_url IS NULL OR launch_url = '' THEN '❌ Missing'
    ELSE '✅ OK'
  END as status
FROM add_ons
WHERE is_active = true
ORDER BY
  CASE WHEN launch_url IS NULL OR launch_url = '' THEN 1 ELSE 0 END,
  name;
