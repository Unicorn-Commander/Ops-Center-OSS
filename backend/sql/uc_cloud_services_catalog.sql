-- ================================================================
-- UC-Cloud Services Catalog - Real Production Services
-- ================================================================
-- This catalog represents actual UC-Cloud hosted services that
-- users can subscribe to and access via your-domain.com
-- Last Updated: 2025-11-01
-- ================================================================

-- Clear existing test/demo data
TRUNCATE TABLE add_ons CASCADE;
TRUNCATE TABLE user_add_ons CASCADE;

-- ================================================================
-- FEATURED SERVICES (Free with Base Subscription)
-- ================================================================

-- Open-WebUI - AI Chat Interface (FREE)
INSERT INTO add_ons (
    name,
    slug,
    description,
    long_description,
    category,
    base_price,
    currency,
    billing_type,
    version,
    author,
    icon_url,
    features,
    is_active,
    is_featured,
    sort_order,
    created_at,
    metadata
) VALUES (
    'Open-WebUI',
    'open-webui',
    'Full-featured AI chat interface with multi-model support',
    E'Open-WebUI is your gateway to AI conversations. This powerful chat interface supports 100+ LLM models from providers like OpenAI, Anthropic, Google, and local models via Ollama.\n\n**Key Features:**\n• Multi-model support with easy switching\n• Unlimited conversation history\n• Document upload and RAG (Retrieval Augmented Generation)\n• Voice input and dictation\n• Custom prompts and templates\n• Team collaboration features\n• API access for integrations\n\n**Perfect For:**\n• Daily AI assistance and research\n• Content creation and editing\n• Code generation and debugging\n• Document analysis\n• Learning and exploration\n\n**Included FREE** with your UC-Cloud subscription.',
    'AI & Chat',
    0.00,
    'USD',
    'monthly',
    '0.3.35',
    'UC-Cloud',
    '/assets/services/openwebui-icon.png',
    '{
        "models": "100+ LLM models supported",
        "history": "Unlimited conversation history",
        "storage": "10GB document storage",
        "api": "Full API access",
        "collaboration": "Team workspaces",
        "highlights": [
            "OpenAI GPT-4, GPT-4 Turbo",
            "Anthropic Claude 3 Opus, Sonnet, Haiku",
            "Google Gemini Pro",
            "Local models via Ollama",
            "Custom model endpoints"
        ],
        "use_cases": [
            "Research and analysis",
            "Content writing",
            "Code generation",
            "Document Q&A",
            "Creative projects"
        ]
    }'::jsonb,
    TRUE,
    TRUE,
    1,
    NOW(),
    '{
        "access_url": "https://chat.your-domain.com",
        "sso_provider": "keycloak",
        "realm": "uchub",
        "requires_api_key": false,
        "included_in_base": true,
        "setup_time": "instant",
        "documentation": "https://docs.your-domain.com/services/open-webui"
    }'::jsonb
);

-- Center-Deep Pro - AI Metasearch (FREE)
INSERT INTO add_ons (
    name,
    slug,
    description,
    long_description,
    category,
    base_price,
    currency,
    billing_type,
    version,
    author,
    icon_url,
    features,
    is_active,
    is_featured,
    sort_order,
    created_at,
    metadata
) VALUES (
    'Center-Deep Pro',
    'center-deep',
    'Privacy-focused AI metasearch with 70+ search engines',
    E'Center-Deep Pro is the ultimate privacy-respecting search platform that aggregates results from 70+ search engines and sources.\n\n**What Makes It Special:**\n• Zero tracking - your searches are private\n• No ads or sponsored results\n• AI-enhanced result ranking\n• Aggregates Google, Bing, DuckDuckGo, and 67+ more engines\n• Specialized search tools for academic, news, and technical content\n\n**Search Categories:**\n• General web search\n• Academic and scholarly articles\n• News from global sources\n• Technical documentation\n• Images and videos\n• Social media monitoring\n\n**Privacy First:**\n• No search history stored\n• No user tracking\n• No data sold to advertisers\n• Tor network compatible\n\n**Included FREE** with your UC-Cloud subscription.',
    'Search & Research',
    0.00,
    'USD',
    'monthly',
    '3.4.0',
    'UC-Cloud',
    '/assets/services/centerdeep-icon.png',
    '{
        "engines": "70+ search engines",
        "privacy": "Zero tracking guarantee",
        "categories": "8 specialized search types",
        "ai_ranking": "GPT-4 powered result ranking",
        "features": [
            "Meta-search aggregation",
            "Academic search (PubMed, arXiv, JSTOR)",
            "News aggregation (RSS, APIs)",
            "Technical docs search",
            "Image and video search",
            "Custom search engines"
        ],
        "privacy_features": [
            "No cookies",
            "No JavaScript tracking",
            "No logs retention",
            "Tor network support",
            "Encrypted queries"
        ]
    }'::jsonb,
    TRUE,
    TRUE,
    4,
    NOW(),
    '{
        "access_url": "https://search.your-domain.com",
        "sso_provider": "authentik",
        "requires_api_key": false,
        "included_in_base": true,
        "setup_time": "instant",
        "documentation": "https://docs.your-domain.com/services/center-deep"
    }'::jsonb
);

-- ================================================================
-- PREMIUM SERVICES (Paid Add-ons)
-- ================================================================

-- Presenton - AI Presentation Generation (PREMIUM)
INSERT INTO add_ons (
    name,
    slug,
    description,
    long_description,
    category,
    base_price,
    currency,
    billing_type,
    version,
    author,
    icon_url,
    features,
    is_active,
    is_featured,
    sort_order,
    created_at,
    metadata
) VALUES (
    'Presenton',
    'presenton',
    'AI-powered presentation generation with web grounding',
    E'Transform ideas into professional presentations in minutes. Presenton uses GPT-4 to research, write, and design stunning slides automatically.\n\n**What It Does:**\n• Generates complete presentations from a single prompt\n• Researches topics using live web data\n• Creates professional designs with your brand colors\n• Exports to PowerPoint, PDF, Google Slides\n• Collaborative editing with team members\n\n**Use Cases:**\n• Business presentations and pitch decks\n• Educational content and lectures\n• Conference talks and webinars\n• Sales proposals and reports\n• Quick status updates and reviews\n\n**AI Features:**\n• GPT-4 content generation\n• Web research integration for up-to-date information\n• Automatic slide layout and design\n• Speaker notes generation\n• Image suggestions and sourcing\n\n**Professional Output:**\n• Export to PPTX (PowerPoint)\n• Export to PDF with animations\n• Publish to Google Slides\n• Share via web link\n• Presenter mode with notes',
    'Productivity',
    19.99,
    'USD',
    'monthly',
    '1.2.0',
    'UC-Cloud',
    '/assets/services/presenton-icon.png',
    '{
        "ai_model": "GPT-4 Turbo",
        "web_research": "Live web grounding",
        "monthly_credits": "100 presentations/month",
        "export_formats": ["PPTX", "PDF", "Google Slides", "Web"],
        "features": [
            "AI content generation",
            "Web research integration",
            "Auto-formatting and design",
            "Theme customization",
            "Collaboration tools",
            "Version history",
            "Presenter mode"
        ],
        "templates": "50+ professional templates",
        "brand_kit": "Custom colors, fonts, logos",
        "team_features": [
            "Shared workspaces",
            "Comment and review",
            "Role-based permissions",
            "Usage analytics"
        ]
    }'::jsonb,
    TRUE,
    TRUE,
    2,
    NOW(),
    '{
        "access_url": "https://presentations.your-domain.com",
        "sso_provider": "keycloak",
        "realm": "uchub",
        "requires_api_key": false,
        "included_in_base": false,
        "setup_time": "instant",
        "trial_period_days": 14,
        "documentation": "https://docs.your-domain.com/services/presenton"
    }'::jsonb
);

-- Bolt.DIY - AI Development Environment (PREMIUM)
INSERT INTO add_ons (
    name,
    slug,
    description,
    long_description,
    category,
    base_price,
    currency,
    billing_type,
    version,
    author,
    icon_url,
    features,
    is_active,
    is_featured,
    sort_order,
    created_at,
    metadata
) VALUES (
    'Bolt.DIY',
    'bolt-diy',
    'AI development environment with instant code generation',
    E'Bolt.DIY is a full-stack AI development environment that generates, edits, and deploys entire applications from natural language descriptions.\n\n**What You Can Build:**\n• Full-stack web applications\n• React and Vue.js frontends\n• Node.js and Python backends\n• REST APIs and microservices\n• Database schemas and migrations\n• Chrome extensions and tools\n\n**AI Superpowers:**\n• Generate entire apps from descriptions\n• Debug and fix code automatically\n• Refactor and optimize existing code\n• Add features with natural language\n• Explain complex code sections\n• Write tests and documentation\n\n**Development Tools:**\n• Live preview with hot reload\n• Built-in terminal and package manager\n• Git integration and version control\n• One-click deployment to cloud\n• Database GUI and query builder\n• API testing and documentation\n\n**Supported Tech:**\n• Languages: JavaScript, TypeScript, Python, Go\n• Frameworks: React, Vue, Next.js, FastAPI\n• Databases: PostgreSQL, MySQL, MongoDB\n• Deployment: Vercel, Netlify, Railway, Fly.io',
    'Development',
    29.99,
    'USD',
    'monthly',
    '2.1.0',
    'UC-Cloud',
    '/assets/services/bolt-icon.png',
    '{
        "ai_model": "GPT-4 + Claude 3 Opus",
        "languages": ["JavaScript", "TypeScript", "Python", "Go", "Rust"],
        "frameworks": ["React", "Vue", "Next.js", "Svelte", "FastAPI", "Express"],
        "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite"],
        "features": [
            "AI code generation",
            "Live preview",
            "Git integration",
            "One-click deploy",
            "Terminal access",
            "Package management",
            "Database GUI",
            "API testing"
        ],
        "monthly_limits": {
            "projects": "Unlimited",
            "ai_generations": "500 per month",
            "deployments": "100 per month",
            "storage": "50GB"
        },
        "deployment_targets": [
            "Vercel",
            "Netlify",
            "Railway",
            "Fly.io",
            "Custom servers"
        ]
    }'::jsonb,
    TRUE,
    TRUE,
    3,
    NOW(),
    '{
        "access_url": "https://bolt.your-domain.com",
        "sso_provider": "keycloak",
        "realm": "uchub",
        "requires_api_key": false,
        "included_in_base": false,
        "setup_time": "instant",
        "trial_period_days": 14,
        "documentation": "https://docs.your-domain.com/services/bolt"
    }'::jsonb
);

-- Unicorn Brigade - Multi-Agent AI Platform (PREMIUM)
INSERT INTO add_ons (
    name,
    slug,
    description,
    long_description,
    category,
    base_price,
    currency,
    billing_type,
    version,
    author,
    icon_url,
    features,
    is_active,
    is_featured,
    sort_order,
    created_at,
    metadata
) VALUES (
    'Unicorn Brigade',
    'brigade',
    'Multi-agent AI platform with 47+ pre-built specialists',
    E'Unicorn Brigade is an advanced multi-agent AI platform that orchestrates teams of specialized AI agents to handle complex workflows and tasks.\n\n**The Brigade Team:**\n• **The General** - Master orchestrator that coordinates all agents\n• **47+ Domain Specialists** - Pre-built experts in finance, legal, medical, cybersecurity, and more\n• **Gunny** - Conversational agent builder that creates custom agents through natural dialogue\n\n**Domain Specialists Include:**\n• Financial Analyst - Market research, portfolio analysis\n• Legal Advisor - Contract review, compliance checking\n• Medical Consultant - Research, diagnosis support\n• Cybersecurity Expert - Threat analysis, vulnerability assessment\n• Data Scientist - Statistical analysis, ML modeling\n• Marketing Strategist - Campaign planning, SEO optimization\n• And 41 more specialists...\n\n**How It Works:**\n1. Describe your complex task to The General\n2. The General assembles the right team of specialists\n3. Agents collaborate using A2A (Agent-to-Agent) protocol\n4. Results are synthesized and delivered\n\n**Build Custom Agents:**\n• Use Gunny to create agents through conversation\n• Define agent capabilities and tools\n• Connect to external APIs and databases\n• Share agents with your team\n\n**Enterprise Features:**\n• Tool library with 12+ integrations\n• Multi-provider LLM support\n• Agent performance analytics\n• Audit logs and compliance\n• Team collaboration workspaces',
    'AI Agents',
    39.99,
    'USD',
    'monthly',
    '1.5.0',
    'UC-Cloud',
    '/assets/services/brigade-icon.png',
    '{
        "orchestrator": "The General (GPT-4 powered)",
        "specialist_agents": 47,
        "agent_builder": "Gunny conversational builder",
        "protocols": ["A2A (Agent-to-Agent)", "Tool use", "Memory persistence"],
        "domain_specialists": [
            "Finance & Investment",
            "Legal & Compliance",
            "Medical & Healthcare",
            "Cybersecurity",
            "Data Science",
            "Marketing & SEO",
            "Software Engineering",
            "Research & Analysis",
            "Customer Support",
            "Project Management"
        ],
        "tool_library": [
            "Web search and scraping",
            "Database queries",
            "API integrations",
            "File processing",
            "Email and notifications",
            "Calendar management",
            "Document generation",
            "Code execution",
            "Image generation",
            "Data visualization",
            "Webhook triggers",
            "Custom tools"
        ],
        "monthly_limits": {
            "orchestrations": "1000 per month",
            "custom_agents": "50 custom agents",
            "tool_calls": "10000 per month",
            "storage": "100GB"
        },
        "collaboration": [
            "Team workspaces",
            "Agent sharing",
            "Role-based access",
            "Audit logging"
        ]
    }'::jsonb,
    TRUE,
    TRUE,
    5,
    NOW(),
    '{
        "access_url": "https://brigade.your-domain.com",
        "sso_provider": "keycloak",
        "realm": "uchub",
        "requires_api_key": false,
        "included_in_base": false,
        "setup_time": "instant",
        "trial_period_days": 14,
        "documentation": "https://docs.your-domain.com/services/brigade"
    }'::jsonb
);

-- ================================================================
-- VOICE SERVICES (Specialized Add-ons)
-- ================================================================

-- Unicorn Amanuensis - Speech-to-Text (STT)
INSERT INTO add_ons (
    name,
    slug,
    description,
    long_description,
    category,
    base_price,
    currency,
    billing_type,
    version,
    author,
    icon_url,
    features,
    is_active,
    is_featured,
    sort_order,
    created_at,
    metadata
) VALUES (
    'Unicorn Amanuensis',
    'amanuensis',
    'Professional speech-to-text with speaker diarization',
    E'Unicorn Amanuensis is a professional-grade speech-to-text service powered by WhisperX, supporting 100+ languages with exceptional accuracy.\n\n**Key Features:**\n• Professional-grade transcription accuracy\n• Speaker diarization (identifies who said what)\n• Word-level timestamps\n• 100+ languages supported\n• Batch processing for large files\n• OpenAI-compatible API\n\n**Perfect For:**\n• Meeting transcription and minutes\n• Podcast and video editing\n• Interview transcription\n• Accessibility and subtitles\n• Voice note dictation\n• Call center analytics\n\n**Technical Specs:**\n• Model: WhisperX (based on OpenAI Whisper)\n• Accuracy: 95%+ for clear audio\n• Speed: Real-time or faster\n• File formats: MP3, WAV, M4A, FLAC, OGG\n• Max file size: 1GB per file\n\n**API Access:**\n• OpenAI-compatible endpoints\n• REST API for integrations\n• Webhook support for callbacks\n• SDKs for Python, JavaScript, Go',
    'Voice Services',
    14.99,
    'USD',
    'monthly',
    '2.0.0',
    'UC-Cloud',
    '/assets/services/amanuensis-icon.png',
    '{
        "model": "WhisperX (Whisper v3 large)",
        "languages": "100+ languages",
        "accuracy": "95%+ for clear audio",
        "features": [
            "Speaker diarization",
            "Word-level timestamps",
            "Batch processing",
            "OpenAI API compatible",
            "Multiple audio formats",
            "Real-time transcription"
        ],
        "monthly_credits": "300 hours/month",
        "supported_formats": ["MP3", "WAV", "M4A", "FLAC", "OGG", "WEBM"],
        "api_features": [
            "REST API",
            "Webhook callbacks",
            "Python SDK",
            "JavaScript SDK",
            "Batch upload"
        ],
        "use_cases": [
            "Meeting transcription",
            "Podcast editing",
            "Video subtitles",
            "Interview notes",
            "Voice memos",
            "Call analytics"
        ]
    }'::jsonb,
    TRUE,
    FALSE,
    6,
    NOW(),
    '{
        "access_url": "https://stt.your-domain.com",
        "api_url": "https://stt.your-domain.com/v1",
        "sso_provider": "authentik",
        "requires_api_key": true,
        "included_in_base": false,
        "setup_time": "instant",
        "trial_period_days": 7,
        "documentation": "https://docs.your-domain.com/services/amanuensis"
    }'::jsonb
);

-- Unicorn Orator - Text-to-Speech (TTS)
INSERT INTO add_ons (
    name,
    slug,
    description,
    long_description,
    category,
    base_price,
    currency,
    billing_type,
    version,
    author,
    icon_url,
    features,
    is_active,
    is_featured,
    sort_order,
    created_at,
    metadata
) VALUES (
    'Unicorn Orator',
    'orator',
    'Multi-voice text-to-speech with emotion control',
    E'Unicorn Orator is a professional text-to-speech service with 20+ realistic voices, emotion control, and SSML support.\n\n**Voice Library:**\n• 20+ professional voices (male and female)\n• Multiple languages and accents\n• Emotion and tone control\n• Speed and pitch adjustment\n• Custom voice training available\n\n**Perfect For:**\n• Audiobook creation\n• Accessibility features\n• IVR and phone systems\n• E-learning content\n• Podcasts and videos\n• Voice assistants and bots\n\n**Advanced Features:**\n• SSML (Speech Synthesis Markup Language) support\n• Emotion control (happy, sad, excited, calm)\n• Speaking style adaptation\n• Background music mixing\n• Batch processing for long content\n• OpenAI-compatible API\n\n**Studio Quality:**\n• 48kHz sample rate\n• Natural prosody and intonation\n• Proper emphasis and pauses\n• Multiple output formats (MP3, WAV, OGG)',
    'Voice Services',
    14.99,
    'USD',
    'monthly',
    '1.8.0',
    'UC-Cloud',
    '/assets/services/orator-icon.png',
    '{
        "voices": "20+ professional voices",
        "languages": "15+ languages",
        "quality": "Studio-grade 48kHz audio",
        "features": [
            "Emotion control",
            "SSML support",
            "Speed adjustment",
            "Pitch control",
            "OpenAI API compatible",
            "Batch processing",
            "Custom voice training"
        ],
        "monthly_credits": "500,000 characters/month",
        "output_formats": ["MP3", "WAV", "OGG", "FLAC"],
        "emotions": [
            "Neutral",
            "Happy",
            "Sad",
            "Excited",
            "Angry",
            "Calm",
            "Whisper"
        ],
        "api_features": [
            "REST API",
            "Streaming audio",
            "Python SDK",
            "JavaScript SDK",
            "Webhook support"
        ],
        "use_cases": [
            "Audiobooks",
            "E-learning",
            "IVR systems",
            "Podcasts",
            "Accessibility",
            "Voice assistants"
        ]
    }'::jsonb,
    TRUE,
    FALSE,
    7,
    NOW(),
    '{
        "access_url": "https://tts.your-domain.com",
        "api_url": "https://tts.your-domain.com/v1",
        "sso_provider": "authentik",
        "requires_api_key": true,
        "included_in_base": false,
        "setup_time": "instant",
        "trial_period_days": 7,
        "documentation": "https://docs.your-domain.com/services/orator"
    }'::jsonb
);

-- ================================================================
-- COMING SOON SERVICES
-- ================================================================

-- MagicDeck - Advanced Presentation Tool (COMING SOON)
INSERT INTO add_ons (
    name,
    slug,
    description,
    long_description,
    category,
    base_price,
    currency,
    billing_type,
    version,
    author,
    icon_url,
    features,
    is_active,
    is_featured,
    sort_order,
    created_at,
    metadata
) VALUES (
    'MagicDeck',
    'magicdeck',
    'Next-gen AI presentation creation with advanced templates',
    E'MagicDeck is the next generation of presentation creation tools, combining AI power with professional design templates and real-time collaboration.\n\n**Coming Soon Features:**\n• AI-powered content generation\n• 100+ professional templates\n• Real-time collaboration\n• Brand kit management\n• Presentation analytics\n• Presenter mode with teleprompter\n• Export to PowerPoint, PDF, Web\n• Integration with other UC-Cloud services\n\n**What Makes It Different:**\n• More templates than Presenton\n• Advanced animation controls\n• Team collaboration features\n• Presenter notes and teleprompter\n• Audience engagement tools\n• Analytics and tracking\n\n**Expected Q1 2026**',
    'Productivity',
    24.99,
    'USD',
    'monthly',
    '1.0.0-beta',
    'UC-Cloud',
    '/assets/services/magicdeck-icon.png',
    '{
        "status": "Coming Q1 2026",
        "templates": "100+ professional templates",
        "collaboration": "Real-time editing",
        "planned_features": [
            "AI content generation",
            "Brand kit",
            "Analytics",
            "Presenter mode",
            "Teleprompter",
            "Audience polls",
            "Live Q&A",
            "Recording"
        ]
    }'::jsonb,
    FALSE,
    FALSE,
    8,
    NOW(),
    '{
        "access_url": "https://magicdeck.your-domain.com",
        "sso_provider": "keycloak",
        "realm": "uchub",
        "requires_api_key": false,
        "included_in_base": false,
        "setup_time": "instant",
        "status": "coming_soon",
        "expected_release": "2026-Q1",
        "documentation": "https://docs.your-domain.com/services/magicdeck"
    }'::jsonb
);

-- ================================================================
-- SERVICE CATEGORIES
-- ================================================================

-- Ensure categories are properly set
UPDATE add_ons SET category = 'AI & Chat' WHERE slug IN ('open-webui');
UPDATE add_ons SET category = 'Productivity' WHERE slug IN ('presenton', 'magicdeck');
UPDATE add_ons SET category = 'Development' WHERE slug IN ('bolt-diy');
UPDATE add_ons SET category = 'Search & Research' WHERE slug IN ('center-deep');
UPDATE add_ons SET category = 'AI Agents' WHERE slug IN ('brigade');
UPDATE add_ons SET category = 'Voice Services' WHERE slug IN ('amanuensis', 'orator');

-- ================================================================
-- PRICING TIERS (for reference)
-- ================================================================

COMMENT ON COLUMN add_ons.base_price IS
'Pricing Strategy:
- $0.00 = Included FREE with base UC-Cloud subscription (Open-WebUI, Center-Deep)
- $14.99 = Voice services (Amanuensis, Orator) - specialized tools
- $19.99 = Entry premium (Presenton) - productivity boost
- $24.99 = Mid-tier premium (MagicDeck) - advanced features
- $29.99 = Professional tools (Bolt.DIY) - development environment
- $39.99 = Enterprise platform (Brigade) - multi-agent orchestration';

-- ================================================================
-- ANALYTICS AND TRACKING
-- ================================================================

-- Add view tracking
CREATE TABLE IF NOT EXISTS service_views (
    id SERIAL PRIMARY KEY,
    addon_id INTEGER REFERENCES add_ons(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    viewed_at TIMESTAMP DEFAULT NOW(),
    source VARCHAR(50), -- 'marketplace', 'dashboard', 'direct'
    user_agent TEXT
);

CREATE INDEX idx_service_views_addon ON service_views(addon_id);
CREATE INDEX idx_service_views_user ON service_views(user_id);
CREATE INDEX idx_service_views_date ON service_views(viewed_at);

-- Add subscription tracking
CREATE TABLE IF NOT EXISTS service_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    addon_id INTEGER REFERENCES add_ons(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'cancelled', 'expired', 'trial'
    trial_ends_at TIMESTAMP,
    is_trial BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, addon_id)
);

CREATE INDEX idx_service_subs_user ON service_subscriptions(user_id);
CREATE INDEX idx_service_subs_addon ON service_subscriptions(addon_id);
CREATE INDEX idx_service_subs_status ON service_subscriptions(status);

-- ================================================================
-- SUMMARY
-- ================================================================

-- Count services by category
SELECT
    category,
    COUNT(*) as service_count,
    COUNT(*) FILTER (WHERE is_featured = TRUE) as featured_count,
    COUNT(*) FILTER (WHERE is_active = TRUE) as active_count,
    COUNT(*) FILTER (WHERE base_price = 0) as free_count
FROM add_ons
GROUP BY category
ORDER BY category;

-- List all services with pricing
SELECT
    name,
    slug,
    category,
    CASE
        WHEN base_price = 0 THEN 'FREE (included)'
        ELSE '$' || base_price || '/' || billing_type
    END as pricing,
    CASE
        WHEN is_active THEN '✅ Active'
        ELSE '🚧 Coming Soon'
    END as status,
    CASE
        WHEN is_featured THEN '⭐ Featured'
        ELSE ''
    END as featured
FROM add_ons
ORDER BY sort_order;
