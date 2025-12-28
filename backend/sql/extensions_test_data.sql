-- ============================================================================
-- Extensions Marketplace Test Data
-- ============================================================================
-- Comprehensive seed data with 15 add-ons across 4 categories
-- Created: November 1, 2025
--
-- Usage:
-- docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /path/to/extensions_test_data.sql
-- ============================================================================

BEGIN;

-- Clear existing test data
DELETE FROM add_on_purchases WHERE add_on_id IN (SELECT id FROM add_ons);
DELETE FROM cart_items WHERE add_on_id IN (SELECT id FROM add_ons);
DELETE FROM promo_codes;
DELETE FROM add_ons;

-- ============================================================================
-- AI/ML Tools Category (4 add-ons)
-- ============================================================================

INSERT INTO add_ons (
    name, slug, description, long_description, category, base_price,
    billing_type, features, is_active, is_featured, sort_order,
    author, version, icon_url, rating, review_count, install_count
) VALUES
(
    'Advanced Analytics Dashboard',
    'analytics-dashboard',
    'Real-time analytics with custom dashboards and AI-powered insights',
    'Transform your data into actionable insights with our advanced analytics dashboard. Features include real-time data visualization, custom KPI tracking, predictive analytics powered by machine learning, and automated report generation. Perfect for data-driven decision making.',
    'Analytics',
    49.99,
    'monthly',
    '{"realtime": "Real-time data updates", "custom_dashboards": "Unlimited custom dashboards", "ai_insights": "AI-powered insights", "export": "Export to PDF/Excel", "alerts": "Smart alerts and notifications"}',
    TRUE,
    TRUE,
    1,
    'Magic Unicorn',
    '2.1.0',
    'https://api.dicebear.com/7.x/shapes/svg?seed=analytics',
    4.8,
    127,
    3450
),
(
    'Neural Network Builder',
    'neural-network-builder',
    'Visual neural network designer with pre-trained models and AutoML',
    'Build, train, and deploy neural networks without writing code. Includes drag-and-drop interface, 50+ pre-trained models, automatic hyperparameter tuning, GPU acceleration support, and one-click deployment to production. Supports TensorFlow, PyTorch, and ONNX formats.',
    'AI/ML Tools',
    99.99,
    'monthly',
    '{"visual_builder": "Drag-and-drop NN builder", "pretrained": "50+ pre-trained models", "automl": "AutoML hyperparameter tuning", "gpu": "GPU acceleration", "deployment": "One-click deployment"}',
    TRUE,
    TRUE,
    2,
    'AI Labs Inc',
    '3.5.2',
    'https://api.dicebear.com/7.x/shapes/svg?seed=neural',
    4.9,
    89,
    1230
),
(
    'Computer Vision Toolkit',
    'cv-toolkit',
    'Complete computer vision solution with object detection and facial recognition',
    'Enterprise-grade computer vision toolkit featuring real-time object detection, facial recognition, image segmentation, OCR, and video analysis. Includes pre-trained models for 1000+ object classes, custom model training, and RESTful API for easy integration.',
    'AI/ML Tools',
    75.00,
    'monthly',
    '{"object_detection": "Real-time object detection", "facial_rec": "Facial recognition", "ocr": "Advanced OCR", "video": "Video stream analysis", "api": "RESTful API"}',
    TRUE,
    FALSE,
    3,
    'Vision AI Corp',
    '1.8.0',
    'https://api.dicebear.com/7.x/shapes/svg?seed=vision',
    4.7,
    156,
    2100
),
(
    'NLP Processing Suite',
    'nlp-suite',
    'Natural language processing with sentiment analysis and entity extraction',
    'Advanced NLP toolkit with 100+ languages support, sentiment analysis, named entity recognition, text classification, language translation, and summarization. Perfect for chatbots, content analysis, and text mining applications.',
    'AI/ML Tools',
    59.99,
    'monthly',
    '{"languages": "100+ languages", "sentiment": "Sentiment analysis", "entities": "Named entity recognition", "translation": "Language translation", "summarization": "Text summarization"}',
    TRUE,
    FALSE,
    4,
    'NLP Solutions',
    '2.3.1',
    'https://api.dicebear.com/7.x/shapes/svg?seed=nlp',
    4.6,
    93,
    1780
),

-- ============================================================================
-- Productivity Category (4 add-ons)
-- ============================================================================

(
    'Smart Workflow Automation',
    'workflow-automation',
    'Automate repetitive tasks with visual workflow builder and AI assistance',
    'Streamline your operations with intelligent workflow automation. Create complex automation sequences without coding using our visual builder. Features include 500+ app integrations, conditional logic, scheduled tasks, webhook triggers, and AI-powered workflow optimization.',
    'Productivity',
    39.99,
    'monthly',
    '{"integrations": "500+ app integrations", "visual_builder": "Visual workflow builder", "scheduling": "Advanced scheduling", "webhooks": "Webhook triggers", "ai_optimize": "AI workflow optimization"}',
    TRUE,
    TRUE,
    5,
    'AutoFlow Inc',
    '4.2.0',
    'https://api.dicebear.com/7.x/shapes/svg?seed=workflow',
    4.7,
    210,
    5230
),
(
    'Team Collaboration Hub',
    'collab-hub',
    'Unified workspace for team communication, file sharing, and project management',
    'All-in-one collaboration platform combining chat, video calls, file storage, task management, and real-time document editing. Features include unlimited storage, end-to-end encryption, guest access, and mobile apps for iOS and Android.',
    'Productivity',
    29.99,
    'monthly',
    '{"chat": "Team chat", "video": "HD video calls", "storage": "Unlimited storage", "tasks": "Project management", "realtime": "Real-time editing"}',
    TRUE,
    TRUE,
    6,
    'CollabCo',
    '5.1.3',
    'https://api.dicebear.com/7.x/shapes/svg?seed=collab',
    4.8,
    342,
    7890
),
(
    'Document Intelligence',
    'doc-intelligence',
    'AI-powered document processing with OCR, classification, and data extraction',
    'Transform unstructured documents into structured data. Automatic document classification, intelligent OCR, data extraction from invoices/receipts/forms, version control, and workflow automation. Supports 50+ document types and formats.',
    'Productivity',
    45.00,
    'monthly',
    '{"ocr": "Intelligent OCR", "classification": "Auto document classification", "extraction": "Data extraction", "formats": "50+ formats", "workflow": "Workflow automation"}',
    TRUE,
    FALSE,
    7,
    'DocAI Labs',
    '1.9.2',
    'https://api.dicebear.com/7.x/shapes/svg?seed=docs',
    4.5,
    78,
    1450
),
(
    'Time Tracking Pro',
    'time-tracking-pro',
    'Automatic time tracking with productivity insights and billing integration',
    'Track time automatically with AI-powered activity detection. Features include automatic project detection, productivity analytics, billable hours tracking, invoicing, team timesheets, and integrations with popular project management tools.',
    'Productivity',
    19.99,
    'monthly',
    '{"auto_tracking": "Automatic time tracking", "analytics": "Productivity insights", "billing": "Billing integration", "invoicing": "Invoice generation", "team": "Team timesheets"}',
    TRUE,
    FALSE,
    8,
    'TimeWise',
    '3.0.5',
    'https://api.dicebear.com/7.x/shapes/svg?seed=time',
    4.4,
    165,
    3200
),

-- ============================================================================
-- Analytics Category (3 add-ons)
-- ============================================================================

(
    'Business Intelligence Suite',
    'bi-suite',
    'Enterprise BI platform with advanced visualization and predictive analytics',
    'Comprehensive business intelligence solution featuring interactive dashboards, ad-hoc reporting, data modeling, predictive analytics, and data warehouse integration. Connect to 100+ data sources including SQL, NoSQL, cloud storage, and APIs.',
    'Analytics',
    89.99,
    'monthly',
    '{"dashboards": "Interactive dashboards", "reporting": "Ad-hoc reporting", "predictive": "Predictive analytics", "sources": "100+ data sources", "warehouse": "Data warehouse integration"}',
    TRUE,
    FALSE,
    9,
    'BI Corp',
    '6.2.1',
    'https://api.dicebear.com/7.x/shapes/svg?seed=bi',
    4.9,
    201,
    4560
),
(
    'Customer Analytics Platform',
    'customer-analytics',
    'Customer behavior analysis with segmentation and lifetime value prediction',
    'Understand your customers with advanced analytics. Features include customer segmentation, churn prediction, lifetime value calculation, cohort analysis, attribution modeling, and personalization recommendations.',
    'Analytics',
    65.00,
    'monthly',
    '{"segmentation": "Customer segmentation", "churn": "Churn prediction", "ltv": "Lifetime value", "cohort": "Cohort analysis", "attribution": "Attribution modeling"}',
    TRUE,
    FALSE,
    10,
    'CustomerMetrics',
    '2.7.0',
    'https://api.dicebear.com/7.x/shapes/svg?seed=customer',
    4.6,
    112,
    2340
),
(
    'Real-Time Metrics Monitor',
    'realtime-metrics',
    'Live system monitoring with custom KPIs and anomaly detection',
    'Monitor your systems in real-time with customizable dashboards. Features include custom metric definitions, anomaly detection using ML, alert rules, historical trend analysis, and integrations with popular monitoring tools.',
    'Analytics',
    35.00,
    'monthly',
    '{"realtime": "Real-time monitoring", "custom_kpis": "Custom KPIs", "anomaly": "ML anomaly detection", "alerts": "Advanced alerting", "integrations": "Tool integrations"}',
    TRUE,
    FALSE,
    11,
    'MetricsIO',
    '1.5.4',
    'https://api.dicebear.com/7.x/shapes/svg?seed=metrics',
    4.5,
    87,
    1890
),

-- ============================================================================
-- Security Category (4 add-ons)
-- ============================================================================

(
    'Enterprise Security Shield',
    'security-shield',
    'Complete security suite with threat detection and compliance management',
    'Protect your infrastructure with enterprise-grade security. Features include real-time threat detection, vulnerability scanning, compliance monitoring (GDPR, HIPAA, SOC2), security audit logs, and incident response automation.',
    'Security',
    99.00,
    'monthly',
    '{"threat_detection": "Real-time threat detection", "vuln_scan": "Vulnerability scanning", "compliance": "GDPR/HIPAA/SOC2", "audit": "Security audit logs", "incident": "Incident response"}',
    TRUE,
    TRUE,
    12,
    'SecureOps',
    '4.8.0',
    'https://api.dicebear.com/7.x/shapes/svg?seed=security',
    4.9,
    178,
    3890
),
(
    'API Security Gateway',
    'api-gateway',
    'API security with rate limiting, authentication, and DDoS protection',
    'Secure your APIs with advanced protection. Features include OAuth 2.0/JWT authentication, rate limiting, DDoS protection, request validation, API monitoring, and analytics. Supports REST, GraphQL, and gRPC.',
    'Security',
    55.00,
    'monthly',
    '{"auth": "OAuth/JWT auth", "rate_limit": "Advanced rate limiting", "ddos": "DDoS protection", "validation": "Request validation", "monitoring": "API monitoring"}',
    TRUE,
    FALSE,
    13,
    'APIShield',
    '2.4.1',
    'https://api.dicebear.com/7.x/shapes/svg?seed=api',
    4.7,
    134,
    2780
),
(
    'Data Encryption Manager',
    'encryption-manager',
    'End-to-end encryption for files, databases, and communications',
    'Encrypt sensitive data at rest and in transit. Features include AES-256 encryption, key management, encrypted file storage, database encryption, secure messaging, and compliance reporting.',
    'Security',
    45.00,
    'monthly',
    '{"encryption": "AES-256 encryption", "key_mgmt": "Key management", "file_storage": "Encrypted storage", "database": "Database encryption", "messaging": "Secure messaging"}',
    TRUE,
    FALSE,
    14,
    'CryptoSafe',
    '3.1.2',
    'https://api.dicebear.com/7.x/shapes/svg?seed=crypto',
    4.6,
    98,
    2100
),
(
    'Identity Access Manager',
    'iam-manager',
    'Centralized identity management with SSO and multi-factor authentication',
    'Manage user identities and access controls. Features include single sign-on (SSO), multi-factor authentication (MFA), role-based access control (RBAC), user provisioning, directory sync (LDAP/AD), and audit trails.',
    'Security',
    69.99,
    'monthly',
    '{"sso": "Single sign-on", "mfa": "Multi-factor auth", "rbac": "Role-based access", "provisioning": "User provisioning", "directory": "LDAP/AD sync"}',
    TRUE,
    FALSE,
    15,
    'IdentityGuard',
    '5.0.3',
    'https://api.dicebear.com/7.x/shapes/svg?seed=identity',
    4.8,
    145,
    3210
);

-- ============================================================================
-- Promotional Codes (5 codes)
-- ============================================================================

INSERT INTO promo_codes (
    code, discount_type, discount_value, usage_limit, times_used,
    valid_from, valid_until, is_active, description
) VALUES
(
    'WELCOME25',
    'percentage',
    25.00,
    1000,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '30 days',
    TRUE,
    'Welcome discount - 25% off first purchase'
),
(
    'SPRING50',
    'percentage',
    50.00,
    500,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '60 days',
    TRUE,
    'Spring sale - 50% off all add-ons'
),
(
    'SAVE20',
    'fixed',
    20.00,
    NULL,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '90 days',
    TRUE,
    'Save $20 on any purchase'
),
(
    'EARLYBIRD',
    'percentage',
    30.00,
    250,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '14 days',
    TRUE,
    'Early bird special - 30% off'
),
(
    'EXPIRED10',
    'percentage',
    10.00,
    100,
    0,
    CURRENT_TIMESTAMP - INTERVAL '30 days',
    CURRENT_TIMESTAMP - INTERVAL '1 day',
    FALSE,
    'Expired test code - 10% off'
);

COMMIT;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Count add-ons by category
SELECT
    category,
    COUNT(*) as count,
    AVG(base_price) as avg_price
FROM add_ons
WHERE is_active = TRUE
GROUP BY category
ORDER BY category;

-- Show featured add-ons
SELECT name, category, base_price, rating, install_count
FROM add_ons
WHERE is_featured = TRUE
ORDER BY sort_order;

-- Show promo codes
SELECT code, discount_type, discount_value, is_active, valid_until
FROM promo_codes
ORDER BY code;

-- Summary statistics
SELECT
    COUNT(*) as total_addons,
    COUNT(CASE WHEN is_featured THEN 1 END) as featured_count,
    AVG(base_price) as avg_price,
    MIN(base_price) as min_price,
    MAX(base_price) as max_price
FROM add_ons
WHERE is_active = TRUE;
