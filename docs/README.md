# Ops-Center Documentation

Comprehensive documentation for the UC-Cloud Ops-Center platform.

**Last Updated**: November 14, 2025

---

## Quick Start

**New to Ops-Center?** Start here:
1. Read [CONSOLIDATION_COMPLETE_SUMMARY.md](./CONSOLIDATION_COMPLETE_SUMMARY.md) - Overview of current features
2. Check [integration/QUICK_REFERENCE_CARD.md](./integration/QUICK_REFERENCE_CARD.md) - Single-page cheat sheet
3. Review [integration/OPS_CENTER_INTEGRATION_GUIDE.md](./integration/OPS_CENTER_INTEGRATION_GUIDE.md) - Full integration guide

---

## Documentation Structure

### 📋 Overview

- **[CONSOLIDATION_COMPLETE_SUMMARY.md](./CONSOLIDATION_COMPLETE_SUMMARY.md)** ⭐ **START HERE**
  - Complete overview of Ops-Center features
  - Recent changes and cleanup work
  - Production readiness status
  - Quick reference for all systems

### 🏗️ Architecture (`architecture/`)

- **[PROVIDER_KEYS_AUDIT_REPORT.md](./architecture/PROVIDER_KEYS_AUDIT_REPORT.md)** (62 KB, 23,000 words)
  - Complete audit of 3 provider key systems
  - Duplication analysis
  - Consolidation recommendations
  - Migration plans

- **[LITELLM_MONITORING_ANALYSIS.md](./architecture/LITELLM_MONITORING_ANALYSIS.md)** (25 KB)
  - LiteLLM container status and configuration
  - Lago integration architecture
  - Built-in monitoring capabilities
  - Provider key flow mapping

### 💰 Billing (`billing/`)

- **[BILLING_SYSTEMS_ANALYSIS.md](./billing/BILLING_SYSTEMS_ANALYSIS.md)** (29 KB)
  - Technical breakdown of 4 billing systems
  - How Lago, Org Credits, Usage Tracking, and LiteLLM work together
  - Database schemas
  - Source code analysis

- **[BILLING_SYSTEMS_FLOWCHART.md](./billing/BILLING_SYSTEMS_FLOWCHART.md)** (38 KB)
  - Visual flow diagrams
  - Monthly billing cycle
  - Decision trees
  - Error scenarios

- **[BILLING_SYSTEMS_QUICK_REFERENCE.md](./billing/BILLING_SYSTEMS_QUICK_REFERENCE.md)** (14 KB)
  - Team cheatsheet
  - API endpoints
  - Error codes
  - Support scenarios

### 🔗 Integration (`integration/`)

- **[OPS_CENTER_INTEGRATION_GUIDE.md](./integration/OPS_CENTER_INTEGRATION_GUIDE.md)** (32 KB, 1,800+ lines)
  - Complete guide for LoopNet Leads and Center-Deep Pro
  - Python, Node.js, and Curl examples
  - Authentication methods
  - Error handling
  - Production-ready code snippets

- **[QUICK_REFERENCE_CARD.md](./integration/QUICK_REFERENCE_CARD.md)** (6 KB)
  - Single-page cheat sheet
  - Essential endpoints
  - Quick code snippets
  - Common errors

---

## Key Features Documented

### Organizational Billing System
- **Hybrid credit pools**: Organizations + individual users
- **1 credit = $0.001 USD** of LLM usage
- **Complementary to Lago**: Not duplicate, works together
- Files: `backend/org_credit_integration.py`

### Multi-Provider LLM Keys
- **7 providers supported**: OpenRouter, OpenAI, Anthropic, HuggingFace, Groq, X.AI, Google
- **Format validation**: Each provider has specific key format
- **Encrypted storage**: Platform_settings table with Fernet encryption
- Files: `backend/platform_keys_api.py`

### Billing & Usage Tracking
- **Lago**: Monthly subscription billing ($19-$99/month)
- **Org Credits**: Pre-paid usage pools (credits)
- **Usage Tracking**: API quotas (100-10k calls/month)
- **LiteLLM**: Token-level cost tracking

### Integration Ready
- **LoopNet Leads**: Company enrichment, contact lookup
- **Center-Deep Pro**: AI search summaries, analysis
- **Internal API**: `http://ops-center-centerdeep:8084/api/v1/llm`

---

## Documentation Stats

**Total Documentation**: 206 KB across 8 major guides
- Architecture: 87 KB (2 guides)
- Billing: 81 KB (3 guides)
- Integration: 38 KB (2 guides)
- Overview: 11 KB (1 guide)

**Lines of Documentation**: ~6,500 lines
**Code Examples**: Python, Node.js, Curl, SQL
**Diagrams**: Flow charts, architecture diagrams, decision trees

---

## Contributing

When adding new documentation:
1. Choose appropriate directory: `architecture/`, `billing/`, `integration/`, or root
2. Use descriptive filenames with `_` separators
3. Include file size and line count in this README
4. Add entry to appropriate section above
5. Update "Last Updated" date at top

---

## Support

For questions about:
- **Architecture**: See `architecture/` docs
- **Billing**: See `billing/` docs
- **Integration**: See `integration/` docs
- **Quick answers**: Check `QUICK_REFERENCE_CARD.md`

---

## Recent Additions (November 14, 2025)

All 8 documentation files created during comprehensive audit and consolidation:
- ✅ Provider key systems audit (3 systems analyzed)
- ✅ Billing systems analysis (4 systems verified as complementary)
- ✅ LiteLLM integration verified (Lago callbacks operational)
- ✅ Integration guides created (LoopNet + Center-Deep)
- ✅ Duplicate UI removed (SystemProviderKeys)
- ✅ All improvements preserved (org credits, validators)

**Status**: Production ready for both centerdeep.online and unicorncommander.ai instances
