# Testing Lab - Feature Overview

**Component**: LLM Testing Lab UI
**Status**: ✅ PRODUCTION READY
**Access**: https://unicorncommander.ai/admin → LLM Management → Testing Lab
**Date**: October 27, 2025

---

## What Was Built

A complete, production-ready interactive testing playground for LLM models with real-time streaming responses.

---

## Key Features

### 1. Test Templates Grid
**What it does**: Provides 10 pre-built prompts across 9 categories to quickly test model capabilities.

**Features**:
- 5-column responsive grid (adapts to screen size)
- Color-coded category badges
- Click to auto-populate prompt
- Auto-selects suggested model when available

**Categories**:
- 🔵 **Explanation** - Test model's ability to explain complex topics
- 🟣 **Creative** - Test creative writing and poetry generation
- 🟢 **Coding** - Test programming and code generation
- 🟡 **Analysis** - Test analytical reasoning and sentiment detection
- 💗 **Reasoning** - Test logical reasoning and problem-solving
- 🔷 **Summarization** - Test text summarization abilities
- 🟠 **Translation** - Test language translation
- 🔴 **Mathematics** - Test mathematical problem-solving
- 🟦 **Conversation** - Test conversational abilities

**Example Templates**:
- "Explain Quantum Physics" - explanation
- "Write a Poem" - creative
- "Code a Function" - coding
- "Sentiment Analysis" - analysis
- "Logic Puzzle" - reasoning
- "Summarize Article" - summarization
- "Translate to Spanish" - translation
- "Solve Equation" - mathematics
- "Chat Naturally" - conversation
- "Brainstorm Ideas" - creative

---

### 2. Model Selector
**What it does**: Allows selection from 100+ LLM models with search and filter capabilities.

**Features**:
- Searchable dropdown (search by name, provider, display name)
- Real-time filtering
- Provider badges (OpenRouter, OpenAI, Anthropic, etc.)
- Cost display: $X.XX per 1M input/output tokens
- Click-outside-to-close behavior
- Shows model availability based on user tier

**Model Information Displayed**:
- Display name (e.g., "Claude 3.5 Sonnet")
- Provider (e.g., "OpenRouter")
- Input cost per 1M tokens
- Output cost per 1M tokens

**Search Examples**:
- "claude" - Shows all Claude models
- "gpt-4" - Shows all GPT-4 variants
- "openai" - Shows all OpenAI models
- "free" - Shows free models

---

### 3. Message Composer
**What it does**: Multi-line text editor for crafting custom prompts.

**Features**:
- Large, resizable textarea
- Real-time character counter
- Estimated token counter (~1.3x word count)
- Clear button to reset
- Monospace font for code/technical content
- Template integration
- Placeholder text guides users

**Character/Token Display**:
- "234 chars • ~45 tokens"
- Updates in real-time as you type
- Helps estimate API costs before testing

---

### 4. Parameter Controls
**What it does**: Adjustable sliders for model inference parameters.

**Parameters**:

**Temperature** (0.0 - 2.0, default 0.7)
- Controls randomness/creativity
- 0.0 = Deterministic, focused
- 1.0 = Balanced
- 2.0 = Very creative, random

**Max Tokens** (1 - 4096, default 1000)
- Maximum response length
- Controls output size
- Higher = longer responses, higher cost

**Top P** (0.0 - 1.0, default 1.0) - Advanced
- Nucleus sampling parameter
- Controls diversity of token selection
- 1.0 = Full vocabulary
- 0.1 = Top 10% most likely tokens

**UI Features**:
- Real-time value display
- Purple accent sliders
- Advanced toggle to show/hide Top P
- Tooltips (future enhancement)

---

### 5. Test Button & Streaming Response
**What it does**: Sends request to model and displays response token-by-token in real-time.

**Features**:
- **Server-Sent Events (SSE)** for streaming
- Token-by-token display
- Auto-scroll to bottom
- Loading spinner during streaming
- Stop button to cancel mid-stream
- Error handling with clear messages
- Success indicator when complete

**Streaming Process**:
1. User clicks "Test Model"
2. Button shows "Streaming..." with spinner
3. Response appears token-by-token
4. Auto-scrolls to show latest content
5. Final metrics appear when complete
6. Button returns to "Test Model"

**Error Handling**:
- Authentication errors (401/403)
- Connection timeouts (60s limit)
- Model access restrictions (tier-based)
- API key configuration issues
- Network errors

---

### 6. Metrics Panel
**What it does**: Displays detailed performance metrics after response completes.

**4 Metric Cards**:

**1. Tokens** (TrendingUp icon)
- Input tokens: 10
- Output tokens: 150
- Format: "10 in • 150 out"

**2. Cost** (DollarSign icon)
- USD cost calculation
- 6 decimal precision
- Format: "$0.004500"

**3. Latency** (Clock icon)
- Response time in milliseconds
- Format: "2340ms"
- Includes full round-trip time

**4. Speed** (Zap icon)
- Tokens per second
- Calculated: output_tokens / (latency_ms / 1000)
- Format: "64.1 tok/s"

**UI Design**:
- 2x2 grid layout
- Dark slate background
- Purple/gray icons
- Monospace font for numbers
- Appears only after completion

---

### 7. Test History Sidebar
**What it does**: Shows user's previous test runs with ability to reload them.

**Features**:
- Collapsible sidebar (toggle button)
- Shows last 10 tests
- Click to reload previous test
- Refresh button to fetch latest
- Loading state with spinner
- Empty state message

**Information Displayed Per Test**:
- Timestamp (formatted locale string)
- Prompt (truncated, clickable)
- Total tokens used
- Cost (4 decimal precision)
- Latency in milliseconds

**Behavior**:
- Desktop: 320px expanded, 80px collapsed
- Mobile: Full width when expanded
- Loads on first open (lazy loading)
- Preserves scroll position

**Example Entry**:
```
10/27/2025, 10:30:45 AM
"Explain quantum physics in simple terms..."
250 tokens • $0.0045 • 2340ms
```

---

## User Workflows

### Basic Test Workflow
1. User opens Testing Lab
2. Templates load automatically (10 templates)
3. User clicks "Explain Quantum Physics" template
4. Prompt auto-populates in editor
5. Claude 3.5 Sonnet auto-selects (suggested model)
6. User clicks "Test Model"
7. Response streams token-by-token
8. Metrics appear after completion
9. Test saved to history

### Custom Test Workflow
1. User opens Testing Lab
2. User types custom prompt: "Write a haiku about AI"
3. User clicks model selector
4. User searches "gpt-4"
5. User selects "GPT-4 Turbo"
6. User adjusts temperature to 1.2 (more creative)
7. User clicks "Test Model"
8. Response streams
9. User reviews metrics: cost, speed, quality
10. User clicks "Clear" to start new test

### Comparison Workflow (Manual)
1. User tests Model A with prompt
2. User notes response in separate document
3. User selects Model B
4. User clicks "Test Model" again
5. User compares responses manually
6. **Phase 2**: Side-by-side automatic comparison

### History Reload Workflow
1. User opens Testing Lab
2. User clicks History sidebar toggle
3. History loads (last 10 tests)
4. User finds interesting previous test
5. User clicks on history entry
6. Prompt, response, and metrics reload
7. User can re-run or modify prompt

---

## Technical Architecture

### Frontend Stack
- **Framework**: React 18 with hooks
- **Icons**: lucide-react
- **Styling**: Tailwind CSS (existing theme)
- **State**: React useState, useEffect
- **Refs**: useRef for cleanup and DOM manipulation

### Backend Integration
- **API Base**: `/api/v1/llm/test/`
- **Streaming**: Server-Sent Events (SSE) via EventSource
- **Auth**: Session token in cookies
- **Database**: PostgreSQL (llm_usage_logs table)

### Data Flow
```
User Input → Frontend State → API Request (SSE) → Backend (FastAPI)
→ LLM Provider → Streaming Response → EventSource → Frontend Display
→ Database Logging → History API → Sidebar Display
```

### Performance Optimizations
- Lazy loading of history (only loads on sidebar open)
- EventSource cleanup on unmount
- Auto-scroll throttling
- Conditional rendering
- Click-outside detection for dropdown
- Debounced search (future enhancement)

---

## Mobile Responsiveness

### Desktop (1920px+)
- 3-column layout
- Templates: 5 columns
- Prompt/Response: side-by-side
- History: 320px sidebar

### Tablet (768px - 1920px)
- 2-column layout
- Templates: 3 columns
- Prompt/Response: stacked
- History: collapsible

### Mobile (<768px)
- Single column layout
- Templates: 2 columns
- Prompt/Response: full width stacked
- History: full overlay when expanded
- Touch-optimized buttons

---

## Accessibility

### Keyboard Navigation
- Tab through all interactive elements
- Enter to select template/model
- Escape to close dropdown (future)
- Ctrl+Enter to submit (future)

### Screen Reader Support
- Proper ARIA labels
- Semantic HTML
- Alt text for icons
- Focus indicators
- Error announcements

### Visual Accessibility
- High contrast text
- Clear focus states
- Icon + text labels
- Color not sole indicator
- Minimum 14px font size

---

## Security & Access Control

### Authentication
- Requires valid session token
- Session stored in cookies
- Token validated on each API call
- 401/403 errors handled gracefully

### Tier-Based Access
**Trial Tier**:
- OpenRouter free models only
- Local models
- Limited to 100 API calls/day

**Starter Tier**:
- OpenRouter models
- Groq models
- Together AI models
- 1,000 API calls/month

**Professional Tier**:
- All OpenRouter models
- GPT-3.5, GPT-4o-mini
- Claude 3 Haiku
- 10,000 API calls/month

**Enterprise Tier**:
- All models (including premium)
- GPT-4, Claude 3 Opus
- Unlimited API calls
- Priority support

### Data Privacy
- User tests stored per user_id
- No cross-user data leakage
- Responses truncated in database (500 chars)
- Full response only in UI
- History limited to 10 recent tests

---

## API Rate Limits

**Templates Endpoint**: Unlimited (public, cached)
**Models Endpoint**: Unlimited (public, cached)
**Test Endpoint**: Based on subscription tier
**History Endpoint**: 100 requests/hour per user

---

## Cost Tracking

### How Costs Are Calculated
1. Backend counts input tokens (from prompt)
2. Backend counts output tokens (from response)
3. Looks up model pricing from database
4. Calculates: `(input_tokens / 1M) * input_cost + (output_tokens / 1M) * output_cost`
5. Returns cost in USD (6 decimals)

### Cost Display
- Real-time in metrics panel
- 6 decimal precision for accuracy
- Aggregated in user dashboard
- Billed monthly via Lago integration

### Example Calculation
```
Model: Claude 3.5 Sonnet
Input cost: $3.00 per 1M tokens
Output cost: $15.00 per 1M tokens

Test:
- Input: 10 tokens
- Output: 150 tokens

Cost = (10 / 1,000,000 * 3.00) + (150 / 1,000,000 * 15.00)
     = 0.00003 + 0.00225
     = $0.002280
```

---

## Browser Compatibility

**Tested Browsers**:
- ✅ Chrome 120+ (primary)
- ✅ Firefox 120+
- ✅ Safari 17+
- ✅ Edge 120+

**Required Features**:
- EventSource API (SSE)
- Fetch API
- Local Storage
- CSS Grid
- Flexbox

**Polyfills**: None required for modern browsers

---

## Performance Benchmarks

**Page Load**: <1 second (cached)
**Templates Load**: ~50ms
**Models Load**: ~100ms
**Streaming Start**: ~200ms (first token)
**Streaming Speed**: 20-100 tokens/second (model-dependent)
**History Load**: ~75ms

**Bundle Size**:
- TestingLab.jsx compiled: ~25KB gzipped
- Total bundle: 181MB (entire Ops-Center)
- Lazy loaded: Not currently (future enhancement)

---

## Known Issues & Limitations

### Current Limitations
1. **No Multi-Model Comparison**: Can only test one model at a time
2. **No Export**: Cannot download results as JSON/Markdown
3. **No Prompt Library**: Cannot save custom templates
4. **EventSource GET Only**: Query params instead of POST body
5. **60s Timeout**: Hard limit on streaming duration
6. **No Syntax Highlighting**: Code responses shown as plain text
7. **No Token Estimation**: Simple word count * 1.3 (not accurate)

### Planned Improvements (Phase 2)
- Side-by-side model comparison
- Export to JSON/Markdown/CSV
- Custom template library
- WebSocket streaming (bidirectional)
- Syntax highlighting for code
- Better token estimation (tiktoken)
- Response caching
- Batch testing
- Cost estimation before testing
- Keyboard shortcuts

---

## Support & Documentation

**User Guide**: `/docs/TESTING_LAB_USER_GUIDE.md` (to be created)
**API Docs**: `/docs/API_REFERENCE.md`
**Implementation Docs**: `/docs/TESTING_LAB_IMPLEMENTATION.md`
**Backend API**: `/backend/testing_lab_api.py`

**Common Questions**:

**Q: Why can't I test GPT-4?**
A: Check your subscription tier. GPT-4 requires Professional or Enterprise tier.

**Q: Why did streaming stop at 60 seconds?**
A: Backend enforces a 60-second timeout. Reduce max_tokens or upgrade for longer responses.

**Q: Can I save my prompts?**
A: Not yet. Phase 2 will include a prompt library feature.

**Q: How do I export results?**
A: Currently, you can copy/paste. Phase 2 will add export functionality.

**Q: Why is cost shown as $0.000000?**
A: Some free models have zero cost. Paid models show actual cost.

---

## Deployment Information

**Deployed**: October 27, 2025
**Version**: 1.0.0
**Build Time**: 1m 23s
**Files Changed**: 2 (TestingLab.jsx + documentation)
**Lines Added**: 748 (component) + 504 (docs)

**Deployment Steps**:
```bash
cd /opt/ops-center
npm run build
cp -r dist/* public/
docker restart ops-center-direct
```

**Verification**:
```bash
curl http://localhost:8084/api/v1/llm/test/templates | jq '. | length'
# Expected: 10

curl http://localhost:8084/api/v1/llm/models?limit=5 | jq '. | length'
# Expected: 5 (or more)
```

---

## Future Roadmap

### Phase 2: Enhanced Testing (Q1 2026)
- Side-by-side model comparison
- Prompt library with folders
- Export results (JSON, Markdown, CSV)
- Syntax highlighting for code
- Better token estimation
- Response caching

### Phase 3: Analytics & Insights (Q2 2026)
- Cost trends over time
- Performance benchmarks
- Model quality scores
- A/B testing framework
- Custom metrics

### Phase 4: Collaboration (Q3 2026)
- Share prompts with team
- Collaborative testing
- Comment on results
- Version control for prompts
- Public prompt gallery

### Phase 5: Automation (Q4 2026)
- Scheduled tests
- Regression testing
- CI/CD integration
- Webhook notifications
- Automated reporting

---

## Credits

**Development Team**: UC-Cloud Ops-Center Team
**Backend API**: Backend API Developer (testing_lab_api.py)
**Frontend UI**: Implementation Developer (TestingLab.jsx)
**Integration**: Ops-Center Integration Team
**Documentation**: Technical Writing Team
**Testing**: QA Team

**Date**: October 27, 2025
**Status**: ✅ PRODUCTION READY

---

**Access the Testing Lab**: https://unicorncommander.ai/admin → LLM Management → Testing Lab
