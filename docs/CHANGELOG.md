# Ops-Center Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2025-11-04

### Added

#### Image Generation API 🎨
- **New Endpoint**: `POST /api/v1/llm/image/generations` - OpenAI-compatible image generation
- **Model Support**: DALL-E 2/3, Stable Diffusion XL/3, and more via OpenRouter
- **BYOK Support**: Users can bring their own OpenAI/OpenRouter API keys (no credits charged)
- **Credit Tracking**: Automatic billing with tier-based pricing multipliers
  - Free tier: 1.5x markup
  - Managed tier: 1.2x markup
  - BYOK/VIP Founder: No markup
- **Quality Options**: Standard and HD quality for DALL-E 3
- **Batch Generation**: Generate up to 10 images per request
- **Multiple Sizes**: Support for various image dimensions from 256x256 to 1792x1024
- **Response Formats**: URL or base64-encoded image data
- **Usage Metering**: Full analytics tracking for image generation costs

#### Request Models
- `ImageGenerationRequest`: Pydantic model for image generation requests
- `ImageGenerationResponse`: Response model with OpenAI compatibility

#### Cost Calculator
- `calculate_image_cost()`: Automatic pricing based on model, size, quality, and user tier
- Support for 4+ image generation models with different pricing tiers

#### Documentation
- Complete API documentation: `/docs/api/IMAGE_GENERATION_API_GUIDE.md` (20+ pages)
- Quick start guide: `/docs/api/IMAGE_GENERATION_QUICK_START.md`
- Integration examples for Python, JavaScript, TypeScript, React, and cURL
- BYOK setup instructions
- Error handling guide
- Rate limits documentation

### Changed
- Updated `litellm_api.py` with 340+ lines of new image generation code
- Enhanced credit system to support image generation billing

### Technical Details
- **Backend Files**: `backend/litellm_api.py` (lines 221-1207)
- **New Dependencies**: None (uses existing httpx, pydantic, fastapi)
- **OpenAI SDK Compatible**: Works as drop-in replacement

### Pricing

| Model | Size | Quality | Cost (Managed Tier) |
|-------|------|---------|---------------------|
| DALL-E 3 | 1024x1024 | Standard | 48 credits (~$0.048) |
| DALL-E 3 | 1024x1024 | HD | 96 credits (~$0.096) |
| DALL-E 2 | 1024x1024 | - | 22 credits (~$0.022) |
| Stable Diffusion XL | 1024x1024 | - | 6 credits (~$0.006) |

### API Examples

#### Python
```python
import openai
openai.api_base = "https://your-domain.com/api/v1/llm"
openai.api_key = "YOUR_UC_API_KEY"

response = openai.Image.create(
    prompt="A majestic unicorn in a magical forest",
    model="dall-e-3",
    size="1024x1024"
)
```

#### JavaScript
```javascript
const response = await fetch('https://your-domain.com/api/v1/llm/image/generations', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_UC_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: 'A majestic unicorn in a magical forest',
    model: 'dall-e-3'
  })
});
```

---

## [2.1.1] - 2025-10-29

### Fixed
- **Credit Display**: Removed misleading dollar signs, now shows "10,000 credits" instead of "$10,000"
- **Credit API Authentication**: Fixed user authentication to use real Keycloak sessions
- **Keycloak Field Mapping**: Added automatic mapping of Keycloak `sub` field to `user_id`

### Changed
- Updated `backend/credit_api.py` with proper session authentication
- Updated `src/pages/CreditDashboard.jsx` with `formatCredits()` function

---

## [2.1.0] - 2025-10-15

### Added
- **User Management System**: Comprehensive user management with 6-tab detail view
- **Bulk Operations**: CSV import/export, bulk role assignment, bulk suspend/delete
- **Advanced Filtering**: 10+ filter options for user list
- **API Key Management**: Full CRUD for user API keys with bcrypt hashing
- **User Impersonation**: Admin "login as user" feature
- **Activity Timeline**: Color-coded audit log with expandable details
- **Role Management**: Enhanced dual-panel UI with visual permission matrix

---

## [2.0.0] - 2025-09-15

### Added
- Initial production release
- LiteLLM API with credit system
- Keycloak SSO integration
- Billing dashboard
- Organization management
- Service management

---

## Links
- **Repository**: https://github.com/Unicorn-Commander/Ops-Center
- **Documentation**: `/docs/`
- **API Guide**: `/docs/api/IMAGE_GENERATION_API_GUIDE.md`
