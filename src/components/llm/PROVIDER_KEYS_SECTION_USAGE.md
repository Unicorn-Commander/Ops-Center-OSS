# ProviderKeysSection Component - Usage Guide

## Overview

`ProviderKeysSection.jsx` is a production-ready React component for managing LLM provider API keys. It provides a complete UI for adding, editing, testing, and deleting API keys for multiple cloud providers.

**Status**: ✅ Production Ready (created October 27, 2025)

---

## Features

### Cloud Providers Supported (8)
1. **OpenRouter** 🔀 - Universal proxy (200+ models) ⭐ Recommended
2. **OpenAI** 🤖 - GPT-4o, GPT-4-turbo, o1-preview
3. **Anthropic** 🧠 - Claude 3.5 Sonnet, Claude 3 Opus/Sonnet/Haiku
4. **Google AI** 🔍 - Gemini 2.0 Flash, Gemini 1.5 Pro/Flash
5. **Cohere** 🌐 - Command R+, Command R, Embed v3
6. **Groq** ⚡ - Ultra-fast inference (500+ tok/s)
7. **Together AI** 🤝 - Open source models (Llama 3, Mistral, Qwen)
8. **Mistral AI** 🌪️ - Mistral Large 2, Mixtral 8x7B, Codestral

### Custom Provider Support
- Add ANY OpenAI-compatible API
- Custom name and base URL
- Works with self-hosted LLMs (vLLM, Ollama, LocalAI)

### Key Features
- ✅ **Add/Edit/Delete** - Full CRUD operations
- ✅ **Show/Hide Keys** - Password field with toggle
- ✅ **Test Connection** - Verify API key validity
- ✅ **Status Indicators** - Database, Environment, Not Set
- ✅ **Get Key Links** - Direct links to provider dashboards
- ✅ **Encryption** - Fernet symmetric encryption before storage
- ✅ **Collapsible** - Can be collapsed to save space
- ✅ **Theme-Aware** - Supports unicorn, light, dark themes

---

## Usage

### Basic Usage

```jsx
import ProviderKeysSection from '../components/ProviderKeysSection';

function LLMManagementPage() {
  const handleKeysChanged = () => {
    console.log('Provider keys updated!');
    // Refresh models list or show notification
  };

  return (
    <div>
      <h1>LLM Management</h1>
      <ProviderKeysSection onKeysChanged={handleKeysChanged} />
    </div>
  );
}
```

### With Custom Props

```jsx
<ProviderKeysSection
  onKeysChanged={() => {
    // Callback when keys are added/updated/deleted
    refreshModelCatalog();
  }}
  collapsible={true}        // Allow section to collapse (default: true)
  defaultExpanded={false}   // Start collapsed (default: true)
/>
```

### Standalone (Non-Collapsible)

```jsx
<ProviderKeysSection
  onKeysChanged={handleKeysChanged}
  collapsible={false}  // Always expanded, no collapse button
/>
```

---

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onKeysChanged` | `function` | `undefined` | Callback fired when keys are added, updated, or deleted |
| `collapsible` | `boolean` | `true` | Whether the section can be collapsed |
| `defaultExpanded` | `boolean` | `true` | Initial collapsed/expanded state (only when `collapsible: true`) |

---

## Backend API Requirements

The component expects these API endpoints to exist:

### List All Providers
```
GET /api/v1/llm/admin/system-keys
```
**Response**:
```json
{
  "providers": [
    {
      "id": "openrouter",
      "provider_type": "openrouter",
      "name": "OpenRouter",
      "key_source": "database",  // "database" | "environment" | "not_set"
      "key_preview": "sk-or-v1-***...***",
      "last_tested": "2025-10-27T20:30:00Z",
      "test_status": "valid"  // "valid" | "failed"
    }
  ]
}
```

### Save/Update Key
```
PUT /api/v1/llm/admin/system-keys/{provider}
```
**Request Body**:
```json
{
  "api_key": "sk-or-v1-...",
  "custom_name": "My Custom Provider",  // Only for custom provider
  "custom_url": "https://api.example.com/v1"  // Only for custom provider
}
```

### Delete Key
```
DELETE /api/v1/llm/admin/system-keys/{provider}
```

### Test Key
```
POST /api/v1/llm/admin/system-keys/{provider}/test
```
**Response**:
```json
{
  "success": true,
  "message": "OpenRouter key is valid!",
  "provider_name": "OpenRouter"
}
```

---

## Provider Information

Each provider card displays:

### OpenRouter (Recommended)
- **Icon**: 🔀
- **Color**: Blue-cyan gradient
- **Description**: Universal proxy - 200+ models (GPT-4o, Claude 3.5, Gemini 2.0)
- **Key Format**: `sk-or-v1-...`
- **Get Key**: https://openrouter.ai/keys

### OpenAI
- **Icon**: 🤖
- **Color**: Green gradient
- **Description**: GPT-4o, GPT-4o-mini, GPT-4-turbo, o1-preview, o1-mini
- **Key Format**: `sk-proj-...`
- **Get Key**: https://platform.openai.com/api-keys

### Anthropic
- **Icon**: 🧠
- **Color**: Purple-pink gradient
- **Description**: Claude 3.5 Sonnet (latest), Claude 3 Opus/Sonnet/Haiku
- **Key Format**: `sk-ant-...`
- **Get Key**: https://console.anthropic.com/settings/keys

### Google AI
- **Icon**: 🔍
- **Color**: Red-orange gradient
- **Description**: Gemini 2.0 Flash, Gemini 1.5 Pro/Flash (2M context)
- **Key Format**: `AIza...`
- **Get Key**: https://aistudio.google.com/apikey

### Cohere
- **Icon**: 🌐
- **Color**: Pink-rose gradient
- **Description**: Command R+, Command R, Embed v3, Rerank
- **Key Format**: `co-...`
- **Get Key**: https://dashboard.cohere.com/api-keys

### Groq
- **Icon**: ⚡
- **Color**: Orange-yellow gradient
- **Description**: Ultra-fast inference - Llama 3, Mixtral, Gemma (500+ tok/s)
- **Key Format**: `gsk_...`
- **Get Key**: https://console.groq.com/keys

### Together AI
- **Icon**: 🤝
- **Color**: Teal-cyan gradient
- **Description**: Open source models - Llama 3, Mistral, Qwen, DeepSeek
- **Key Format**: `together-...`
- **Get Key**: https://api.together.xyz/settings/api-keys

### Mistral AI
- **Icon**: 🌪️
- **Color**: Indigo-purple gradient
- **Description**: Mistral Large 2, Mixtral 8x7B, Codestral (code generation)
- **Key Format**: `mistral-...`
- **Get Key**: https://console.mistral.ai/api-keys

### Custom Provider
- **Icon**: ⚙️
- **Color**: Gray-slate gradient
- **Description**: Self-hosted or custom LLM endpoint
- **Key Format**: Custom
- **Requires**: Custom name + API base URL

---

## User Workflow

### Adding a Key

1. User sees provider card with "Add Key" button (if not configured)
2. Clicks "Add Key"
3. Modal opens with:
   - Link to get API key (for built-in providers)
   - Input field for API key (password field with show/hide)
   - Custom fields (for custom provider only)
   - Security note: "🔒 Key will be encrypted with Fernet before storage"
4. User enters key
5. Clicks "Save Key"
6. Backend encrypts and stores key
7. Modal closes, list refreshes
8. Status changes to "Database" badge
9. `onKeysChanged()` callback fires

### Testing a Key

1. User sees provider card with "Test" button (if key configured)
2. Clicks "Test"
3. Button shows spinner: "Testing..."
4. Backend validates key with provider
5. Toast notification shows result:
   - ✅ Success: "OpenRouter key is valid!"
   - ❌ Error: "Key validation failed"
6. Status icon updates (✅ or ❌)
7. Last tested timestamp updates

### Editing a Key

1. User clicks edit button (pencil icon)
2. Modal opens with same fields
3. Previous key NOT shown (security)
4. User enters new key
5. Saves (same flow as adding)

### Deleting a Key

1. User clicks delete button (trash icon) - only for database keys
2. Confirmation modal appears
3. User confirms deletion
4. Backend removes key from database
5. Status changes to "Environment" (if env var exists) or "Not Set"
6. Toast shows: "OpenRouter key deleted. Will use environment fallback."

---

## Status Indicators

### 🟢 Database Badge (Green)
- Key configured through UI and stored in PostgreSQL
- Preferred source
- Can be deleted via UI

### 🟡 Environment Badge (Yellow)
- Key loaded from environment variable (.env)
- Fallback source
- Cannot be deleted via UI (read-only)

### 🔴 Not Set Badge (Red)
- No key configured
- Provider unavailable
- "Add Key" button shown

---

## Security Notes

1. **Encryption**: All API keys are encrypted using Fernet symmetric encryption before storage
2. **Password Fields**: Keys hidden by default, show/hide toggle available
3. **No Logging**: Keys never logged or transmitted in plain text
4. **Key Preview**: Only shows first/last few characters (e.g., `sk-or-v1-***...***abc`)
5. **HTTPS**: All API calls encrypted in transit
6. **Priority**: Database keys override environment keys

---

## Theme Support

The component adapts to three themes:

### Unicorn Theme (Purple)
- Purple gradient backgrounds
- White text with purple accents
- Glassmorphic cards with backdrop blur

### Light Theme
- White backgrounds
- Gray text with blue accents
- Clean, minimal design

### Dark Theme
- Slate gray backgrounds
- Light text with blue accents
- High contrast

**Theme Context**: Uses `useTheme()` hook from `ThemeContext`

---

## Integration Example: LLM Management Page

```jsx
import React, { useState } from 'react';
import ProviderKeysSection from '../components/ProviderKeysSection';
import ModelCatalog from '../components/ModelCatalog';

function LLMManagement() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleKeysChanged = () => {
    // Refresh the model catalog when keys change
    setRefreshKey(prev => prev + 1);

    // Show success notification
    console.log('Provider keys updated! Refreshing model catalog...');
  };

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">LLM Management</h1>

      {/* Provider Keys Section */}
      <ProviderKeysSection
        onKeysChanged={handleKeysChanged}
        collapsible={true}
        defaultExpanded={true}
      />

      {/* Model Catalog (refreshes when keys change) */}
      <ModelCatalog key={refreshKey} />
    </div>
  );
}

export default LLMManagement;
```

---

## Troubleshooting

### Keys Not Saving

**Symptom**: Save button doesn't work or shows error

**Solutions**:
1. Check backend API is running:
   ```bash
   curl http://localhost:8084/api/v1/llm/admin/system-keys
   ```
2. Check browser console for errors
3. Verify user has admin permissions
4. Check PostgreSQL connection

### Test Connection Fails

**Symptom**: "Key validation failed" even with valid key

**Solutions**:
1. Verify key format matches provider (e.g., OpenRouter uses `sk-or-v1-`)
2. Check API rate limits with provider
3. Ensure backend can reach provider API (no firewall blocking)
4. Check provider dashboard for key status

### Status Stuck on "Environment"

**Symptom**: Can't change to "Database" status

**Solutions**:
1. Delete environment variable from `.env` file
2. Restart backend container
3. Add key via UI (will override environment)

### Modal Won't Close

**Symptom**: Modal remains open after saving

**Solutions**:
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear React state (may need to reload page)
3. Check browser console for JavaScript errors

---

## File Locations

**Component**: `/opt/ops-center/src/components/ProviderKeysSection.jsx`

**Backend APIs**:
- `/opt/ops-center/backend/llm_provider_keys_api.py` (assumed)
- `/opt/ops-center/backend/server.py` (main FastAPI app)

**Database**: `unicorn_db` (PostgreSQL)
- Table: `llm_provider_keys` (assumed)

---

## Related Components

- `ModelCatalog.jsx` - Displays available models from configured providers
- `APIKeysManager.jsx` - User API keys (different from provider keys)
- `BYOKWizard.jsx` - BYOK (Bring Your Own Key) setup wizard

---

## Future Enhancements

**Potential improvements** (not yet implemented):

1. **Batch Import**: Import multiple keys at once via CSV
2. **Key Rotation**: Schedule automatic key rotation
3. **Usage Tracking**: Show API calls per provider
4. **Cost Monitoring**: Track spending per provider
5. **Key Expiry**: Warn when keys are about to expire
6. **Provider Health**: Show provider status (operational, degraded, down)
7. **Key Sharing**: Share keys across organizations (with permissions)

---

## Testing Checklist

- [ ] Load component - shows all 8 providers + custom
- [ ] Add key for OpenRouter - saves successfully
- [ ] Test key - validates and shows success toast
- [ ] Edit key - modal opens with empty field
- [ ] Delete key - confirmation modal, deletes successfully
- [ ] Show/hide toggle - reveals/hides API key
- [ ] Collapse section - minimizes to header
- [ ] Expand section - shows full content
- [ ] Theme switching - unicorn/light/dark all work
- [ ] Custom provider - can add name + URL + key
- [ ] Status badges - Database/Environment/Not Set display correctly
- [ ] Get key links - open correct provider dashboards
- [ ] onKeysChanged callback - fires on add/edit/delete

---

## License

MIT License - Part of UC-Cloud Ops-Center

**Company**: Magic Unicorn Unconventional Technology & Stuff Inc
**Website**: https://unicorncommander.com

---

## Support

For questions or issues:
1. Check this usage guide first
2. Review backend API logs: `docker logs ops-center-direct -f`
3. Check browser console for errors
4. Review Ops-Center documentation: `/services/ops-center/CLAUDE.md`
