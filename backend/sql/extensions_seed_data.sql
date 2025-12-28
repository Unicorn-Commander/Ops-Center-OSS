-- Extensions Marketplace Seed Data
-- Pre-configured 9 Add-ons for Phase 1 MVP
-- Database: PostgreSQL (unicorn_db)
-- Created: 2025-11-01

-- ============================================================================
-- SEED DATA FOR add_ons TABLE (9 Pre-configured Add-ons)
-- ============================================================================

-- 1. TTS - Unicorn Orator (Text-to-Speech)
INSERT INTO add_ons (name, description, category, base_price, billing_type, features, metadata)
VALUES (
    'Unicorn Orator - TTS',
    'Advanced text-to-speech with multiple voices and languages. Transform text into natural-sounding speech with customizable voice profiles, emotion control, and SSML support.',
    'ai-services',
    9.99,
    'monthly',
    '["tts_enabled", "voice_cloning", "multi_language_tts", "ssml_support"]'::jsonb,
    '{
        "voices": ["neural", "standard", "premium"],
        "languages": 30,
        "monthly_minutes": 10000,
        "api_access": true,
        "priority_processing": false
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- 2. STT - Amanuensis (Speech-to-Text)
INSERT INTO add_ons (name, description, category, base_price, billing_type, features, metadata)
VALUES (
    'Amanuensis - STT',
    'High-accuracy speech-to-text transcription with speaker diarization, punctuation, and real-time streaming. Supports multiple languages and audio formats.',
    'ai-services',
    9.99,
    'monthly',
    '["stt_enabled", "speaker_diarization", "real_time_transcription", "multi_language_stt"]'::jsonb,
    '{
        "accuracy": "95%+",
        "languages": 25,
        "monthly_hours": 100,
        "real_time": true,
        "batch_processing": true
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- 3. Brigade - Agent Platform
INSERT INTO add_ons (name, description, category, base_price, billing_type, features, metadata)
VALUES (
    'Brigade - AI Agent Platform',
    'Deploy and manage multiple AI agents for automated workflows, task orchestration, and intelligent automation. Includes agent templates, scheduling, and monitoring.',
    'ai-services',
    19.99,
    'monthly',
    '["brigade_access", "agent_orchestration", "workflow_automation", "multi_agent_coordination"]'::jsonb,
    '{
        "max_agents": 10,
        "concurrent_tasks": 50,
        "agent_templates": 20,
        "custom_agents": true,
        "monitoring_dashboard": true,
        "api_access": true
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- 4. Bolt - AI Development Environment
INSERT INTO add_ons (name, description, category, base_price, billing_type, features, metadata)
VALUES (
    'Bolt - AI Dev Environment',
    'Complete AI-powered development environment with code generation, debugging, and deployment tools. Integrated with GitHub, containerization, and CI/CD pipelines.',
    'development',
    14.99,
    'monthly',
    '["bolt_access", "code_generation", "ai_debugging", "github_integration", "container_deployment"]'::jsonb,
    '{
        "ide_access": true,
        "gpu_hours": 20,
        "storage_gb": 50,
        "github_repos": "unlimited",
        "docker_containers": 5,
        "ci_cd_minutes": 1000
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- 5. Presenton - AI Presentation Builder
INSERT INTO add_ons (name, description, category, base_price, billing_type, features, metadata)
VALUES (
    'Presenton - Presentation Builder',
    'Create stunning presentations with AI assistance. Automatic slide generation, design suggestions, data visualization, and export to PowerPoint, PDF, or web formats.',
    'productivity',
    9.99,
    'monthly',
    '["presenton_access", "ai_slide_generation", "template_library", "data_visualization"]'::jsonb,
    '{
        "monthly_presentations": 50,
        "templates": 100,
        "custom_branding": true,
        "export_formats": ["pptx", "pdf", "html", "video"],
        "collaboration": true,
        "storage_gb": 10
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- 6. Center-Deep Pro - Advanced Search
INSERT INTO add_ons (name, description, category, base_price, billing_type, features, metadata)
VALUES (
    'Center-Deep Pro - Advanced Search',
    'Enterprise-grade search and analytics powered by vector embeddings, semantic search, and AI-powered insights. Search across documents, code, and data with natural language.',
    'analytics',
    19.99,
    'monthly',
    '["center_deep_access", "semantic_search", "vector_embeddings", "ai_insights", "advanced_analytics"]'::jsonb,
    '{
        "search_queries": 10000,
        "indexed_documents": 100000,
        "vector_dimensions": 1536,
        "embedding_models": ["openai", "cohere", "custom"],
        "api_access": true,
        "real_time_indexing": true
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- 7. Document Processing Suite
INSERT INTO add_ons (name, description, category, base_price, billing_type, features, metadata)
VALUES (
    'Document Processing Suite',
    'Comprehensive document processing with OCR, extraction, classification, and transformation. Handle PDFs, images, Word docs, and more with AI-powered intelligence.',
    'productivity',
    12.99,
    'monthly',
    '["document_processing", "ocr_enabled", "data_extraction", "document_classification"]'::jsonb,
    '{
        "monthly_pages": 5000,
        "ocr_languages": 50,
        "formats": ["pdf", "docx", "jpg", "png", "tiff"],
        "batch_processing": true,
        "api_access": true,
        "extraction_fields": "unlimited"
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- 8. Vector Search Engine
INSERT INTO add_ons (name, description, category, base_price, billing_type, features, metadata)
VALUES (
    'Vector Search Engine',
    'High-performance vector database and similarity search for embeddings, recommendations, and semantic search. Integrated with popular ML frameworks and embedding models.',
    'infrastructure',
    14.99,
    'monthly',
    '["vector_search", "similarity_search", "embedding_storage", "hybrid_search"]'::jsonb,
    '{
        "max_vectors": 1000000,
        "dimensions": 2048,
        "query_speed": "<10ms",
        "storage_gb": 100,
        "backup_enabled": true,
        "api_access": true,
        "distance_metrics": ["cosine", "euclidean", "dot_product"]
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- 9. GPU Compute Access
INSERT INTO add_ons (name, description, category, base_price, billing_type, features, metadata)
VALUES (
    'GPU Compute Access',
    'Dedicated GPU compute resources for AI model training, inference, and high-performance computing. Access to NVIDIA A100, H100, and other enterprise GPUs.',
    'infrastructure',
    49.99,
    'monthly',
    '["gpu_compute", "model_training", "high_performance_inference", "gpu_priority_queue"]'::jsonb,
    '{
        "gpu_hours": 50,
        "gpu_types": ["A100", "H100", "V100"],
        "memory_gb": 80,
        "concurrent_jobs": 3,
        "storage_gb": 500,
        "framework_support": ["pytorch", "tensorflow", "jax", "cuda"]
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- SEED DATA FOR add_on_features TABLE
-- Maps add-ons to specific feature flags they enable
-- ============================================================================

-- Get the add-on IDs for feature mapping
WITH addon_ids AS (
    SELECT id, name FROM add_ons
)

-- TTS - Unicorn Orator features
INSERT INTO add_on_features (add_on_id, feature_key, enabled, configuration)
SELECT id, 'tts_enabled', TRUE, '{"priority": "standard"}'::jsonb
FROM addon_ids WHERE name = 'Unicorn Orator - TTS'
UNION ALL
SELECT id, 'voice_cloning', TRUE, '{"max_clones": 3}'::jsonb
FROM addon_ids WHERE name = 'Unicorn Orator - TTS'
UNION ALL
SELECT id, 'multi_language_tts', TRUE, '{"languages": 30}'::jsonb
FROM addon_ids WHERE name = 'Unicorn Orator - TTS'
UNION ALL
SELECT id, 'ssml_support', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Unicorn Orator - TTS'

-- STT - Amanuensis features
UNION ALL
SELECT id, 'stt_enabled', TRUE, '{"priority": "standard"}'::jsonb
FROM addon_ids WHERE name = 'Amanuensis - STT'
UNION ALL
SELECT id, 'speaker_diarization', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Amanuensis - STT'
UNION ALL
SELECT id, 'real_time_transcription', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Amanuensis - STT'
UNION ALL
SELECT id, 'multi_language_stt', TRUE, '{"languages": 25}'::jsonb
FROM addon_ids WHERE name = 'Amanuensis - STT'

-- Brigade features
UNION ALL
SELECT id, 'brigade_access', TRUE, '{"tier": "standard"}'::jsonb
FROM addon_ids WHERE name = 'Brigade - AI Agent Platform'
UNION ALL
SELECT id, 'agent_orchestration', TRUE, '{"max_agents": 10}'::jsonb
FROM addon_ids WHERE name = 'Brigade - AI Agent Platform'
UNION ALL
SELECT id, 'workflow_automation', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Brigade - AI Agent Platform'
UNION ALL
SELECT id, 'multi_agent_coordination', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Brigade - AI Agent Platform'

-- Bolt features
UNION ALL
SELECT id, 'bolt_access', TRUE, '{"tier": "standard"}'::jsonb
FROM addon_ids WHERE name = 'Bolt - AI Dev Environment'
UNION ALL
SELECT id, 'code_generation', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Bolt - AI Dev Environment'
UNION ALL
SELECT id, 'ai_debugging', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Bolt - AI Dev Environment'
UNION ALL
SELECT id, 'github_integration', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Bolt - AI Dev Environment'
UNION ALL
SELECT id, 'container_deployment', TRUE, '{"max_containers": 5}'::jsonb
FROM addon_ids WHERE name = 'Bolt - AI Dev Environment'

-- Presenton features
UNION ALL
SELECT id, 'presenton_access', TRUE, '{"tier": "standard"}'::jsonb
FROM addon_ids WHERE name = 'Presenton - Presentation Builder'
UNION ALL
SELECT id, 'ai_slide_generation', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Presenton - Presentation Builder'
UNION ALL
SELECT id, 'template_library', TRUE, '{"count": 100}'::jsonb
FROM addon_ids WHERE name = 'Presenton - Presentation Builder'
UNION ALL
SELECT id, 'data_visualization', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Presenton - Presentation Builder'

-- Center-Deep Pro features
UNION ALL
SELECT id, 'center_deep_access', TRUE, '{"tier": "pro"}'::jsonb
FROM addon_ids WHERE name = 'Center-Deep Pro - Advanced Search'
UNION ALL
SELECT id, 'semantic_search', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Center-Deep Pro - Advanced Search'
UNION ALL
SELECT id, 'vector_embeddings', TRUE, '{"dimensions": 1536}'::jsonb
FROM addon_ids WHERE name = 'Center-Deep Pro - Advanced Search'
UNION ALL
SELECT id, 'ai_insights', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Center-Deep Pro - Advanced Search'
UNION ALL
SELECT id, 'advanced_analytics', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Center-Deep Pro - Advanced Search'

-- Document Processing features
UNION ALL
SELECT id, 'document_processing', TRUE, '{"monthly_pages": 5000}'::jsonb
FROM addon_ids WHERE name = 'Document Processing Suite'
UNION ALL
SELECT id, 'ocr_enabled', TRUE, '{"languages": 50}'::jsonb
FROM addon_ids WHERE name = 'Document Processing Suite'
UNION ALL
SELECT id, 'data_extraction', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Document Processing Suite'
UNION ALL
SELECT id, 'document_classification', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Document Processing Suite'

-- Vector Search features
UNION ALL
SELECT id, 'vector_search', TRUE, '{"max_vectors": 1000000}'::jsonb
FROM addon_ids WHERE name = 'Vector Search Engine'
UNION ALL
SELECT id, 'similarity_search', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Vector Search Engine'
UNION ALL
SELECT id, 'embedding_storage', TRUE, '{"storage_gb": 100}'::jsonb
FROM addon_ids WHERE name = 'Vector Search Engine'
UNION ALL
SELECT id, 'hybrid_search', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'Vector Search Engine'

-- GPU Compute features
UNION ALL
SELECT id, 'gpu_compute', TRUE, '{"hours": 50}'::jsonb
FROM addon_ids WHERE name = 'GPU Compute Access'
UNION ALL
SELECT id, 'model_training', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'GPU Compute Access'
UNION ALL
SELECT id, 'high_performance_inference', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'GPU Compute Access'
UNION ALL
SELECT id, 'gpu_priority_queue', TRUE, '{}'::jsonb
FROM addon_ids WHERE name = 'GPU Compute Access'

ON CONFLICT (add_on_id, feature_key) DO NOTHING;

-- ============================================================================
-- SEED DATA FOR promotional_codes TABLE
-- Sample promotional codes for launch
-- ============================================================================

INSERT INTO promotional_codes (code, discount_type, discount_value, max_uses, expires_at, metadata)
VALUES
    ('LAUNCH2025', 'percentage', 20.00, 100, NOW() + INTERVAL '30 days', '{"campaign": "product_launch"}'::jsonb),
    ('FIRSTBUY', 'percentage', 15.00, NULL, NOW() + INTERVAL '90 days', '{"first_purchase_only": true}'::jsonb),
    ('FRIEND50', 'fixed_amount', 5.00, 1000, NOW() + INTERVAL '60 days', '{"referral_program": true}'::jsonb),
    ('VIP2025', 'percentage', 30.00, 50, NOW() + INTERVAL '365 days', '{"tier_required": "vip_founder"}'::jsonb)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- SEED DATA FOR add_on_bundles TABLE
-- Pre-configured bundles with discounts
-- ============================================================================

-- AI Productivity Bundle (TTS + STT + Presenton)
INSERT INTO add_on_bundles (name, description, add_on_ids, discount_percent, metadata)
SELECT
    'AI Productivity Bundle',
    'Complete productivity suite with TTS, STT, and presentation tools',
    ARRAY(
        SELECT id FROM add_ons
        WHERE name IN ('Unicorn Orator - TTS', 'Amanuensis - STT', 'Presenton - Presentation Builder')
    ),
    15.00,
    '{"original_price": 29.97, "bundle_price": 25.47, "savings": 4.50}'::jsonb
WHERE EXISTS (SELECT 1 FROM add_ons WHERE name IN ('Unicorn Orator - TTS', 'Amanuensis - STT', 'Presenton - Presentation Builder'))
ON CONFLICT DO NOTHING;

-- Developer Pro Bundle (Brigade + Bolt + Vector Search)
INSERT INTO add_on_bundles (name, description, add_on_ids, discount_percent, metadata)
SELECT
    'Developer Pro Bundle',
    'Complete development toolkit with agents, IDE, and vector search',
    ARRAY(
        SELECT id FROM add_ons
        WHERE name IN ('Brigade - AI Agent Platform', 'Bolt - AI Dev Environment', 'Vector Search Engine')
    ),
    20.00,
    '{"original_price": 49.97, "bundle_price": 39.98, "savings": 9.99}'::jsonb
WHERE EXISTS (SELECT 1 FROM add_ons WHERE name IN ('Brigade - AI Agent Platform', 'Bolt - AI Dev Environment', 'Vector Search Engine'))
ON CONFLICT DO NOTHING;

-- Enterprise Suite (All AI Services)
INSERT INTO add_on_bundles (name, description, add_on_ids, discount_percent, metadata)
SELECT
    'Enterprise Suite',
    'Complete enterprise package with all AI services and infrastructure',
    ARRAY(SELECT id FROM add_ons WHERE is_active = TRUE),
    25.00,
    '{"tier": "enterprise", "includes_support": true}'::jsonb
WHERE EXISTS (SELECT 1 FROM add_ons WHERE is_active = TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- VERIFY SEED DATA
-- ============================================================================

-- Count inserted records
DO $$
DECLARE
    addon_count INTEGER;
    feature_count INTEGER;
    promo_count INTEGER;
    bundle_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO addon_count FROM add_ons;
    SELECT COUNT(*) INTO feature_count FROM add_on_features;
    SELECT COUNT(*) INTO promo_count FROM promotional_codes;
    SELECT COUNT(*) INTO bundle_count FROM add_on_bundles;

    RAISE NOTICE 'Seed data loaded successfully:';
    RAISE NOTICE '  - Add-ons: %', addon_count;
    RAISE NOTICE '  - Features: %', feature_count;
    RAISE NOTICE '  - Promotional codes: %', promo_count;
    RAISE NOTICE '  - Bundles: %', bundle_count;
END $$;

-- Seed data complete
