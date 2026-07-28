-- ============================================================================
-- Extensions Marketplace Simple Test Data
-- ============================================================================
-- 15 add-ons across 4 categories for testing
-- Compatible with existing add_ons table structure (integer IDs)
-- ============================================================================

BEGIN;

-- Clear existing test data (keep real data safe)
DELETE FROM add_on_purchases WHERE add_on_id < 1000;
DELETE FROM cart_items WHERE add_on_id < 1000;
DELETE FROM add_ons WHERE id < 1000;

-- Reset sequence if needed
SELECT setval('add_ons_id_seq', 1, false);

-- ============================================================================
-- Add-ons Data
-- ============================================================================

INSERT INTO add_ons (
    name, slug, description, category, base_price, billing_type, features,
    is_active, is_featured, sort_order, author, version, icon_url, rating, review_count, install_count
) VALUES
-- AI/ML Tools (4)
('Advanced Analytics Dashboard', 'analytics-dashboard', 'Real-time analytics with custom dashboards and AI-powered insights', 'Analytics', 49.99, 'monthly', '{"realtime": true, "ai_insights": true, "custom_dashboards": true}', TRUE, TRUE, 1, 'Magic Unicorn', '2.1.0', 'https://api.dicebear.com/7.x/shapes/svg?seed=analytics', 4.8, 127, 3450),
('Neural Network Builder', 'neural-network-builder', 'Visual neural network designer with pre-trained models and AutoML', 'AI/ML Tools', 99.99, 'monthly', '{"visual_builder": true, "pretrained": 50, "automl": true}', TRUE, TRUE, 2, 'AI Labs Inc', '3.5.2', 'https://api.dicebear.com/7.x/shapes/svg?seed=neural', 4.9, 89, 1230),
('Computer Vision Toolkit', 'cv-toolkit', 'Complete computer vision solution with object detection and facial recognition', 'AI/ML Tools', 75.00, 'monthly', '{"object_detection": true, "facial_rec": true, "ocr": true}', TRUE, FALSE, 3, 'Vision AI Corp', '1.8.0', 'https://api.dicebear.com/7.x/shapes/svg?seed=vision', 4.7, 156, 2100),
('NLP Processing Suite', 'nlp-suite', 'Natural language processing with sentiment analysis and entity extraction', 'AI/ML Tools', 59.99, 'monthly', '{"languages": 100, "sentiment": true, "entities": true}', TRUE, FALSE, 4, 'NLP Solutions', '2.3.1', 'https://api.dicebear.com/7.x/shapes/svg?seed=nlp', 4.6, 93, 1780),

-- Productivity (4)
('Smart Workflow Automation', 'workflow-automation', 'Automate repetitive tasks with visual workflow builder and AI assistance', 'Productivity', 39.99, 'monthly', '{"integrations": 500, "visual_builder": true, "ai_optimize": true}', TRUE, TRUE, 5, 'AutoFlow Inc', '4.2.0', 'https://api.dicebear.com/7.x/shapes/svg?seed=workflow', 4.7, 210, 5230),
('Team Collaboration Hub', 'collab-hub', 'Unified workspace for team communication, file sharing, and project management', 'Productivity', 29.99, 'monthly', '{"chat": true, "video": true, "storage": "unlimited"}', TRUE, TRUE, 6, 'CollabCo', '5.1.3', 'https://api.dicebear.com/7.x/shapes/svg?seed=collab', 4.8, 342, 7890),
('Document Intelligence', 'doc-intelligence', 'AI-powered document processing with OCR, classification, and data extraction', 'Productivity', 45.00, 'monthly', '{"ocr": true, "classification": true, "extraction": true}', TRUE, FALSE, 7, 'DocAI Labs', '1.9.2', 'https://api.dicebear.com/7.x/shapes/svg?seed=docs', 4.5, 78, 1450),
('Time Tracking Pro', 'time-tracking-pro', 'Automatic time tracking with productivity insights and billing integration', 'Productivity', 19.99, 'monthly', '{"auto_tracking": true, "analytics": true, "billing": true}', TRUE, FALSE, 8, 'TimeWise', '3.0.5', 'https://api.dicebear.com/7.x/shapes/svg?seed=time', 4.4, 165, 3200),

-- Analytics (3)
('Business Intelligence Suite', 'bi-suite', 'Enterprise BI platform with advanced visualization and predictive analytics', 'Analytics', 89.99, 'monthly', '{"dashboards": true, "predictive": true, "sources": 100}', TRUE, FALSE, 9, 'BI Corp', '6.2.1', 'https://api.dicebear.com/7.x/shapes/svg?seed=bi', 4.9, 201, 4560),
('Customer Analytics Platform', 'customer-analytics', 'Customer behavior analysis with segmentation and lifetime value prediction', 'Analytics', 65.00, 'monthly', '{"segmentation": true, "churn": true, "ltv": true}', TRUE, FALSE, 10, 'CustomerMetrics', '2.7.0', 'https://api.dicebear.com/7.x/shapes/svg?seed=customer', 4.6, 112, 2340),
('Real-Time Metrics Monitor', 'realtime-metrics', 'Live system monitoring with custom KPIs and anomaly detection', 'Analytics', 35.00, 'monthly', '{"realtime": true, "custom_kpis": true, "anomaly": true}', TRUE, FALSE, 11, 'MetricsIO', '1.5.4', 'https://api.dicebear.com/7.x/shapes/svg?seed=metrics', 4.5, 87, 1890),

-- Security (4)
('Enterprise Security Shield', 'security-shield', 'Complete security suite with threat detection and compliance management', 'Security', 99.00, 'monthly', '{"threat_detection": true, "vuln_scan": true, "compliance": "GDPR/HIPAA/SOC2"}', TRUE, TRUE, 12, 'SecureOps', '4.8.0', 'https://api.dicebear.com/7.x/shapes/svg?seed=security', 4.9, 178, 3890),
('API Security Gateway', 'api-gateway', 'API security with rate limiting, authentication, and DDoS protection', 'Security', 55.00, 'monthly', '{"auth": "OAuth/JWT", "rate_limit": true, "ddos": true}', TRUE, FALSE, 13, 'APIShield', '2.4.1', 'https://api.dicebear.com/7.x/shapes/svg?seed=api', 4.7, 134, 2780),
('Data Encryption Manager', 'encryption-manager', 'End-to-end encryption for files, databases, and communications', 'Security', 45.00, 'monthly', '{"encryption": "AES-256", "key_mgmt": true, "database": true}', TRUE, FALSE, 14, 'CryptoSafe', '3.1.2', 'https://api.dicebear.com/7.x/shapes/svg?seed=crypto', 4.6, 98, 2100),
('Identity Access Manager', 'iam-manager', 'Centralized identity management with SSO and multi-factor authentication', 'Security', 69.99, 'monthly', '{"sso": true, "mfa": true, "rbac": true}', TRUE, FALSE, 15, 'IdentityGuard', '5.0.3', 'https://api.dicebear.com/7.x/shapes/svg?seed=identity', 4.8, 145, 3210);

COMMIT;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Count by category
SELECT
    category,
    COUNT(*) as count,
    AVG(base_price) as avg_price,
    MIN(base_price) as min_price,
    MAX(base_price) as max_price
FROM add_ons
WHERE is_active = TRUE AND id < 1000
GROUP BY category
ORDER BY category;

-- Featured add-ons
SELECT id, name, category, base_price, rating, install_count
FROM add_ons
WHERE is_featured = TRUE AND id < 1000
ORDER BY sort_order;

-- Summary
SELECT
    COUNT(*) as total_addons,
    COUNT(CASE WHEN is_featured THEN 1 END) as featured_count,
    ROUND(AVG(base_price), 2) as avg_price,
    MIN(base_price) as min_price,
    MAX(base_price) as max_price
FROM add_ons
WHERE is_active = TRUE AND id < 1000;
