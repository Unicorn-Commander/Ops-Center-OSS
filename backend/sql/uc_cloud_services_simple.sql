-- ================================================================
-- UC-Cloud Services Catalog - Simple Version (Schema-Compatible)
-- ================================================================
-- Real UC-Cloud hosted services for user marketplace
-- Compatible with existing add_ons table schema
-- Last Updated: 2025-11-01
-- ================================================================

-- Clear existing data
TRUNCATE TABLE add_ons CASCADE;

-- ================================================================
-- FEATURED SERVICES (Free with Base Subscription)
-- ================================================================

-- Open-WebUI - AI Chat Interface (FREE)
INSERT INTO add_ons (
    name, slug, description, long_description, category, base_price, currency,
    billing_type, version, author, icon_url, features, is_active, is_featured, sort_order
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
        "document_upload": "PDF, DOCX, TXT support",
        "voice_input": "Speech-to-text dictation",
        "custom_prompts": "Save reusable templates",
        "team_features": "Share conversations",
        "api_access": "REST API for integrations",
        "access_url": "https://chat.unicorncommander.ai"
    }'::jsonb,
    TRUE,
    TRUE,
    1
);

-- Center-Deep Pro - AI Metasearch Engine (FREE)
INSERT INTO add_ons (
    name, slug, description, long_description, category, base_price, currency,
    billing_type, version, author, icon_url, features, is_active, is_featured, sort_order
) VALUES (
    'Center-Deep Pro',
    'center-deep',
    'Privacy-focused AI metasearch engine querying 70+ sources',
    E'Center-Deep Pro is an advanced metasearch engine that queries 70+ search engines simultaneously, providing comprehensive results while protecting your privacy.\n\n**Key Features:**\n• 70+ search engines (Google, Bing, DuckDuckGo, etc.)\n• AI-powered result ranking and deduplication\n• Privacy-first: No tracking, no ads\n• Academic research tools\n• Deep search for in-depth queries\n• Report generation\n• API access for tool integration\n\n**Perfect For:**\n• Research and investigation\n• Fact-checking and verification\n• Academic and scholarly work\n• Privacy-conscious searching\n• Comprehensive information gathering\n\n**Included FREE** with your UC-Cloud subscription.',
    'Search & Research',
    0.00,
    'USD',
    'monthly',
    '1.0.0',
    'UC-Cloud',
    '/assets/services/centerdeep-icon.png',
    '{
        "search_engines": "70+ sources",
        "ai_ranking": "Smart result deduplication",
        "privacy": "No tracking or ads",
        "academic": "Scholarly search tools",
        "deep_search": "In-depth research mode",
        "reports": "Auto-generated reports",
        "api_access": "OpenAI-compatible API",
        "access_url": "https://search.unicorncommander.ai"
    }'::jsonb,
    TRUE,
    TRUE,
    2
);

-- ================================================================
-- PREMIUM SERVICES
-- ================================================================

-- Presenton - AI Presentation Generation
INSERT INTO add_ons (
    name, slug, description, long_description, category, base_price, currency,
    billing_type, version, author, icon_url, features, is_active, is_featured, sort_order
) VALUES (
    'Presenton',
    'presenton',
    'AI-powered presentation generation with web grounding',
    E'Presenton transforms your ideas into professional presentations using AI. Simply describe what you need, and Presenton generates beautiful slides with content, images, and layouts.\n\n**Key Features:**\n• AI content generation with GPT-4\n• Web grounding for accurate facts\n• Professional templates\n• Auto-generated speaker notes\n• Export to PPTX, PDF, Google Slides\n• Image search and integration\n• Custom branding support\n\n**Perfect For:**\n• Business presentations\n• Academic lectures\n• Sales pitches\n• Training materials\n• Conference talks\n\n**Premium Service** - $19.99/month',
    'Productivity',
    19.99,
    'USD',
    'monthly',
    '1.2.0',
    'UC-Cloud',
    '/assets/services/presenton-icon.png',
    '{
        "ai_powered": "GPT-4 content generation",
        "web_grounding": "Fact-checked content",
        "templates": "Professional designs",
        "speaker_notes": "Auto-generated notes",
        "export": ["PPTX", "PDF", "Google Slides"],
        "images": "Smart image search",
        "branding": "Custom themes and logos",
        "access_url": "https://presentations.unicorncommander.ai"
    }'::jsonb,
    TRUE,
    TRUE,
    3
);

-- Bolt.DIY - AI Development Environment
INSERT INTO add_ons (
    name, slug, description, long_description, category, base_price, currency,
    billing_type, version, author, icon_url, features, is_active, is_featured, sort_order
) VALUES (
    'Bolt.DIY',
    'bolt-diy',
    'AI-powered full-stack development environment in your browser',
    E'Bolt.DIY is an AI coding assistant that helps you build web applications directly in your browser. From simple prototypes to complex apps, Bolt writes code, sets up environments, and deploys your projects.\n\n**Key Features:**\n• AI code generation (GPT-4, Claude)\n• In-browser development environment\n• One-click deployment\n• Real-time preview\n• Full-stack support (React, Node.js, Python)\n• Git integration\n• Database setup automation\n\n**Perfect For:**\n• Rapid prototyping\n• Learning web development\n• Building MVPs\n• Hackathon projects\n• Client demos\n\n**Premium Service** - $29.99/month',
    'Development',
    29.99,
    'USD',
    'monthly',
    '0.0.4',
    'UC-Cloud',
    '/assets/services/bolt-icon.png',
    '{
        "ai_coding": "GPT-4 and Claude support",
        "environment": "Browser-based IDE",
        "deployment": "One-click to production",
        "preview": "Live code preview",
        "frameworks": ["React", "Node.js", "Python", "Vue"],
        "git": "GitHub integration",
        "databases": "Auto-setup MongoDB, PostgreSQL",
        "access_url": "https://bolt.unicorncommander.ai"
    }'::jsonb,
    TRUE,
    TRUE,
    4
);

-- Unicorn Brigade - Multi-Agent AI Platform
INSERT INTO add_ons (
    name, slug, description, long_description, category, base_price, currency,
    billing_type, version, author, icon_url, features, is_active, is_featured, sort_order
) VALUES (
    'Unicorn Brigade',
    'brigade',
    'Build and deploy AI agents for automation and workflows',
    E'Unicorn Brigade is your agent factory. Create custom AI agents through conversation with Gunny, or choose from 47+ pre-built specialists for finance, legal, medical, cybersecurity, and more.\n\n**Key Features:**\n• The General: Multi-agent orchestrator\n• Gunny: Conversational agent builder\n• 47+ pre-built specialist agents\n• A2A protocol for agent communication\n• Tool library (12+ integrations)\n• Real-time monitoring\n• API access for automation\n\n**Perfect For:**\n• Workflow automation\n• Custom AI assistants\n• Team augmentation\n• Research and analysis\n• Complex multi-step tasks\n\n**Premium Service** - $39.99/month',
    'AI Agents',
    39.99,
    'USD',
    'monthly',
    '1.0.0',
    'UC-Cloud',
    '/assets/services/brigade-icon.png',
    '{
        "agents": "47+ pre-built specialists",
        "builder": "Gunny conversational builder",
        "orchestrator": "The General coordinator",
        "a2a_protocol": "Agent-to-agent communication",
        "tools": "12+ built-in integrations",
        "monitoring": "Real-time performance tracking",
        "api": "Full REST API access",
        "access_url": "https://brigade.unicorncommander.ai"
    }'::jsonb,
    TRUE,
    FALSE,
    5
);

-- Amanuensis - Professional Speech-to-Text
INSERT INTO add_ons (
    name, slug, description, long_description, category, base_price, currency,
    billing_type, version, author, icon_url, features, is_active, is_featured, sort_order
) VALUES (
    'Unicorn Amanuensis',
    'amanuensis',
    'Professional speech-to-text with speaker diarization',
    E'Unicorn Amanuensis provides professional-grade speech-to-text transcription with WhisperX. Supports 100+ languages with word-level timestamps and speaker diarization.\n\n**Key Features:**\n• WhisperX AI engine\n• 100+ language support\n• Speaker diarization (who said what)\n• Word-level timestamps\n• OpenAI API compatibility\n• Batch processing\n• Multiple audio formats\n\n**Perfect For:**\n• Meeting transcription\n• Interview documentation\n• Podcast transcription\n• Lecture notes\n• Legal depositions\n\n**Premium Service** - $14.99/month',
    'Voice Services',
    14.99,
    'USD',
    'monthly',
    '1.0.0',
    'UC-Cloud',
    '/assets/services/amanuensis-icon.png',
    '{
        "engine": "WhisperX professional",
        "languages": "100+ supported",
        "diarization": "Speaker identification",
        "timestamps": "Word-level precision",
        "api": "OpenAI-compatible",
        "batch": "Bulk processing",
        "formats": ["MP3", "WAV", "M4A", "OGG"],
        "access_url": "https://stt.unicorncommander.ai"
    }'::jsonb,
    TRUE,
    FALSE,
    6
);

-- Orator - Professional Text-to-Speech
INSERT INTO add_ons (
    name, slug, description, long_description, category, base_price, currency,
    billing_type, version, author, icon_url, features, is_active, is_featured, sort_order
) VALUES (
    'Unicorn Orator',
    'orator',
    'Professional text-to-speech with 20+ voices and emotion control',
    E'Unicorn Orator delivers studio-quality voice synthesis with 20+ professional voices. Control emotion, pacing, and pronunciation for natural-sounding audio.\n\n**Key Features:**\n• 20+ professional voices\n• Emotion control (happy, sad, excited, calm)\n• SSML support for fine control\n• Multiple languages\n• OpenAI API compatibility\n• MP3/WAV export\n• Commercial use license\n\n**Perfect For:**\n• Audiobook narration\n• Video voiceovers\n• Podcast intros/outros\n• E-learning content\n• Accessibility tools\n\n**Premium Service** - $14.99/month',
    'Voice Services',
    14.99,
    'USD',
    'monthly',
    '1.0.0',
    'UC-Cloud',
    '/assets/services/orator-icon.png',
    '{
        "voices": "20+ professional options",
        "emotion": "Happy, sad, excited, calm",
        "ssml": "Advanced pronunciation control",
        "languages": "10+ language support",
        "api": "OpenAI-compatible",
        "export": ["MP3", "WAV"],
        "license": "Commercial use included",
        "access_url": "https://tts.unicorncommander.ai"
    }'::jsonb,
    TRUE,
    FALSE,
    7
);

-- MagicDeck - Presentation Creation Tool (Coming Soon)
INSERT INTO add_ons (
    name, slug, description, long_description, category, base_price, currency,
    billing_type, version, author, icon_url, features, is_active, is_featured, sort_order
) VALUES (
    'MagicDeck',
    'magicdeck',
    'AI-powered presentation creation and design tool',
    E'MagicDeck combines AI content generation with professional design tools to create stunning presentations. Perfect for teams that need both creativity and consistency.\n\n**Key Features:**\n• AI slide generation\n• Professional templates\n• Team collaboration\n• Brand consistency tools\n• Animation and transitions\n• Export to multiple formats\n• Asset library\n\n**Perfect For:**\n• Marketing teams\n• Sales presentations\n• Corporate communications\n• Design agencies\n• Educational institutions\n\n**Coming Soon** - $24.99/month',
    'Productivity',
    24.99,
    'USD',
    'monthly',
    '0.9.0',
    'UC-Cloud',
    '/assets/services/magicdeck-icon.png',
    '{
        "ai_generation": "Smart slide creation",
        "templates": "100+ professional designs",
        "collaboration": "Real-time team editing",
        "branding": "Brand kit management",
        "animations": "Professional transitions",
        "export": ["PPTX", "PDF", "HTML"],
        "assets": "Stock photo library",
        "status": "coming_soon"
    }'::jsonb,
    FALSE,
    FALSE,
    8
);

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Show summary of loaded services
SELECT
    category,
    COUNT(*) as service_count,
    SUM(CASE WHEN is_featured THEN 1 ELSE 0 END) as featured_count,
    SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_count,
    SUM(CASE WHEN base_price = 0 THEN 1 ELSE 0 END) as free_count
FROM add_ons
GROUP BY category
ORDER BY category;

-- Show all services with key details
SELECT
    name,
    slug,
    category,
    CASE
        WHEN base_price = 0 THEN 'FREE'
        ELSE '$' || base_price::text || '/mo'
    END as pricing,
    CASE
        WHEN is_active THEN 'Active'
        ELSE 'Coming Soon'
    END as status,
    CASE
        WHEN is_featured THEN 'Yes'
        ELSE 'No'
    END as featured
FROM add_ons
ORDER BY sort_order;
