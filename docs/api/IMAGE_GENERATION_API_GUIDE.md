# Image Generation API - Integration Guide

**Ops-Center Image Generation API** provides OpenAI-compatible image generation with flexible pricing, BYOK support, and credit tracking.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Endpoint Details](#endpoint-details)
3. [Request Format](#request-format)
4. [Response Format](#response-format)
5. [Supported Models](#supported-models)
6. [Pricing & Credits](#pricing--credits)
7. [BYOK (Bring Your Own Key)](#byok-bring-your-own-key)
8. [Code Examples](#code-examples)
9. [Error Handling](#error-handling)
10. [Rate Limits](#rate-limits)

---

## Quick Start

### Basic Image Generation

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A majestic unicorn in a magical forest at sunset",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard",
    "n": 1
  }'
```

### Response

```json
{
  "created": 1699123456,
  "data": [
    {
      "url": "https://oaidalleapiprodscus.blob.core.windows.net/private/...",
      "revised_prompt": "A majestic unicorn with a flowing mane..."
    }
  ],
  "_metadata": {
    "provider_used": "OpenRouter",
    "cost_incurred": 40.0,
    "credits_remaining": 9960.0,
    "images_generated": 1,
    "size": "1024x1024",
    "quality": "standard",
    "user_tier": "managed"
  }
}
```

---

## Endpoint Details

**Base URL**: `https://unicorncommander.ai/api/v1/llm`

**Endpoint**: `POST /image/generations`

**Authentication**:
- **Header**: `Authorization: Bearer YOUR_API_KEY`
- **Cookie**: Session-based auth for browser clients

**Content-Type**: `application/json`

**Rate Limits**: Varies by subscription tier (see [Rate Limits](#rate-limits))

---

## Request Format

### Request Body

```typescript
{
  "prompt": string,           // REQUIRED: Image description (1-4000 characters)
  "model": string,            // OPTIONAL: Model to use (default: "dall-e-3")
  "n": number,                // OPTIONAL: Number of images (1-10, default: 1)
  "size": string,             // OPTIONAL: Image dimensions (default: "1024x1024")
  "quality": string,          // OPTIONAL: "standard" or "hd" (DALL-E 3 only)
  "style": string,            // OPTIONAL: "vivid" or "natural" (DALL-E 3 only)
  "response_format": string   // OPTIONAL: "url" or "b64_json" (default: "url")
}
```

### Field Details

#### `prompt` (required)
- **Type**: String
- **Length**: 1-4000 characters
- **Description**: Natural language description of the desired image
- **Tips**:
  - Be specific and descriptive
  - Include style, mood, colors, composition details
  - DALL-E 3 may revise your prompt for safety/quality

**Example Good Prompts**:
```
"A photorealistic portrait of a programmer working late at night,
 dramatic desk lamp lighting, multiple monitors showing code,
 cyberpunk aesthetic with neon accents"

"Minimalist logo design for a tech startup, geometric shapes,
 gradients of blue and purple, modern and clean, white background"

"Oil painting in the style of Van Gogh, a futuristic cityscape
 with flying cars, swirling night sky, vibrant colors"
```

#### `model` (optional)
- **Type**: String
- **Default**: `"dall-e-3"`
- **Options**:
  - `dall-e-3` - Highest quality, best prompt adherence (default)
  - `dall-e-2` - Faster, more affordable
  - `stable-diffusion-xl` - Open-source, creative styles
  - `stable-diffusion-3` - Latest SD version with better quality
  - (More models available via OpenRouter BYOK)

#### `n` (optional)
- **Type**: Integer
- **Range**: 1-10
- **Default**: 1
- **Note**: DALL-E 3 supports `n=1` only; use DALL-E 2 or Stable Diffusion for batches

#### `size` (optional)
- **Type**: String
- **Default**: `"1024x1024"`
- **Options**:
  - **DALL-E 3**: `1024x1024`, `1792x1024` (landscape), `1024x1792` (portrait)
  - **DALL-E 2**: `256x256`, `512x512`, `1024x1024`
  - **Stable Diffusion**: `512x512`, `1024x1024`, `1536x1536`

#### `quality` (optional, DALL-E 3 only)
- **Type**: String
- **Default**: `"standard"`
- **Options**:
  - `standard` - Good quality, faster generation, lower cost (40 credits)
  - `hd` - Enhanced details, sharper, higher cost (80 credits)

#### `style` (optional, DALL-E 3 only)
- **Type**: String
- **Default**: Automatic
- **Options**:
  - `vivid` - Hyper-real, dramatic, cinematic (default for most prompts)
  - `natural` - Subtle, realistic, less dramatic

#### `response_format` (optional)
- **Type**: String
- **Default**: `"url"`
- **Options**:
  - `url` - Returns HTTPS URL to generated image (expires in 1 hour)
  - `b64_json` - Returns base64-encoded image data (for immediate use)

---

## Response Format

### Success Response (HTTP 200)

```json
{
  "created": 1699123456,
  "data": [
    {
      "url": "https://...",
      "revised_prompt": "Enhanced version of your prompt (DALL-E 3 only)",
      "b64_json": "iVBORw0KGgoAAAANS..." // Only if response_format=b64_json
    }
  ],
  "_metadata": {
    "provider_used": "OpenRouter",
    "cost_incurred": 40.0,
    "credits_remaining": 9960.0,
    "transaction_id": "txn_abc123",
    "user_tier": "managed",
    "using_byok": false,
    "byok_provider": null,
    "images_generated": 1,
    "size": "1024x1024",
    "quality": "standard"
  }
}
```

### Response Fields

- **`created`**: Unix timestamp of generation
- **`data`**: Array of generated images
  - **`url`**: HTTPS URL to image (valid for 1 hour)
  - **`b64_json`**: Base64-encoded image (if `response_format=b64_json`)
  - **`revised_prompt`**: DALL-E 3's interpretation of your prompt
- **`_metadata`**: Ops-Center specific metadata
  - **`provider_used`**: Provider that generated the image
  - **`cost_incurred`**: Credits charged (0 if using BYOK)
  - **`credits_remaining`**: Your remaining credit balance
  - **`transaction_id`**: Transaction ID for billing (null if BYOK)
  - **`user_tier`**: Your subscription tier
  - **`using_byok`**: Whether you used your own API key
  - **`images_generated`**: Number of images created
  - **`size`**: Image dimensions
  - **`quality`**: Quality level used

---

## Supported Models

### DALL-E 3 (Recommended)

**Model ID**: `dall-e-3`

**Best For**:
- High-quality photorealistic images
- Complex prompts with specific requirements
- Professional use cases
- When prompt adherence is critical

**Features**:
- Advanced prompt interpretation
- Automatic prompt enhancement
- Superior detail and coherence
- Supports `quality` and `style` parameters

**Limitations**:
- Can only generate 1 image per request (`n=1`)
- Higher cost (40-80 credits per image)

**Sizes**: `1024x1024`, `1792x1024`, `1024x1792`

**Pricing**:
- Standard quality: **40 credits** ($0.04)
- HD quality: **80 credits** ($0.08)
- Landscape/portrait: **80-120 credits** ($0.08-$0.12)

---

### DALL-E 2

**Model ID**: `dall-e-2`

**Best For**:
- Batch generation (multiple images)
- Quick iterations
- Lower-cost experimentation
- Simple prompts

**Features**:
- Faster generation
- Supports batch generation (`n` up to 10)
- More affordable

**Limitations**:
- Lower quality than DALL-E 3
- Less prompt adherence
- No `quality` or `style` parameters

**Sizes**: `256x256`, `512x512`, `1024x1024`

**Pricing**:
- 256x256: **16 credits** ($0.016)
- 512x512: **16 credits** ($0.016)
- 1024x1024: **18 credits** ($0.018)

---

### Stable Diffusion XL

**Model ID**: `stable-diffusion-xl`

**Best For**:
- Artistic styles
- Creative freedom
- Lower costs
- Open-source enthusiasts

**Features**:
- Excellent for artistic styles
- Very affordable
- Fast generation
- Creative interpretations

**Limitations**:
- Less photorealistic than DALL-E
- Prompt adherence varies
- Requires more prompt engineering

**Sizes**: `512x512`, `1024x1024`, `1536x1536`

**Pricing**:
- 512x512: **2 credits** ($0.002)
- 1024x1024: **5 credits** ($0.005)
- 1536x1536: **8 credits** ($0.008)

---

### Stable Diffusion 3

**Model ID**: `stable-diffusion-3`

**Best For**:
- Latest SD improvements
- Better quality than SDXL
- Still very affordable

**Features**:
- Improved quality over SDXL
- Better prompt understanding
- Enhanced details

**Sizes**: `512x512`, `1024x1024`, `1536x1536`

**Pricing**:
- 512x512: **3 credits** ($0.003)
- 1024x1024: **6 credits** ($0.006)
- 1536x1536: **10 credits** ($0.010)

---

## Pricing & Credits

### Credit System

**1 credit = $0.001 USD**

All image generation costs are calculated based on:
1. **Model used** (DALL-E 3 vs DALL-E 2 vs Stable Diffusion)
2. **Image size** (larger = more expensive)
3. **Quality** (HD costs 2x standard)
4. **Number of images** (`n` parameter)
5. **User tier** (tier multipliers apply)

### Tier Multipliers

| Tier | Multiplier | Description |
|------|-----------|-------------|
| **Free** | 1.5x | 50% markup on all models |
| **BYOK** | 0x | No markup - you pay provider directly |
| **Managed** | 1.2x | 20% markup for managed service |
| **VIP Founder** | 1.0x | No markup for founders |

### Example Cost Calculations

#### DALL-E 3 Standard (1024x1024) on Managed Tier

```
Base cost: $0.040
Tier multiplier: 1.2x (managed)
Total cost: $0.040 × 1.2 = $0.048
Credits charged: 48 credits
```

#### Stable Diffusion XL (1024x1024) on Free Tier

```
Base cost: $0.005
Tier multiplier: 1.5x (free)
Total cost: $0.005 × 1.5 = $0.0075
Credits charged: 7.5 credits
```

#### DALL-E 3 HD (1024x1024) on VIP Founder Tier

```
Base cost: $0.080
Tier multiplier: 1.0x (VIP)
Total cost: $0.080 × 1.0 = $0.080
Credits charged: 80 credits
```

### Checking Your Balance

```bash
curl -X GET https://unicorncommander.ai/api/v1/llm/credits \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:
```json
{
  "user_id": "user_abc123",
  "credits_remaining": 9960.0,
  "tier": "managed",
  "monthly_cap": 50000.0
}
```

---

## BYOK (Bring Your Own Key)

### What is BYOK?

BYOK allows you to use **your own API keys** from OpenAI, OpenRouter, or other providers, avoiding credit charges entirely.

### Benefits

✅ **No markup** - Pay provider's rates directly
✅ **No credit tracking** - Unlimited usage with your key
✅ **Provider flexibility** - Use any OpenAI-compatible provider
✅ **Cost control** - Manage billing directly with provider

### How to Enable BYOK

#### 1. Add Your API Key

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/byok/keys \
  -H "Authorization: Bearer YOUR_UC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openrouter",
    "api_key": "sk-or-v1-your-openrouter-key",
    "metadata": {
      "note": "My personal OpenRouter key"
    }
  }'
```

#### 2. Use Image Generation (No Credits Charged!)

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer YOUR_UC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic city",
    "model": "dall-e-3"
  }'
```

Response `_metadata`:
```json
{
  "using_byok": true,
  "byok_provider": "openrouter",
  "cost_incurred": 0.0,
  "credits_remaining": 10000.0  // Unchanged
}
```

### Supported BYOK Providers

| Provider | Image Models | Setup |
|----------|-------------|-------|
| **OpenRouter** | DALL-E 2/3, SD, Midjourney, more | Get key at https://openrouter.ai/keys |
| **OpenAI** | DALL-E 2/3 | Get key at https://platform.openai.com/api-keys |
| **Replicate** | Stable Diffusion, SDXL, more | Get key at https://replicate.com/account/api-tokens |

### BYOK Routing Logic

1. **If you have OpenRouter BYOK key** → Uses OpenRouter for ALL models
2. **If you have OpenAI BYOK key + request DALL-E** → Uses OpenAI directly
3. **Otherwise** → Uses Ops-Center managed service (charges credits)

---

## Code Examples

### Python (OpenAI SDK Compatible)

```python
import openai

# Configure for Ops-Center
openai.api_base = "https://unicorncommander.ai/api/v1/llm"
openai.api_key = "your-uc-api-key"

# Generate image
response = openai.Image.create(
    prompt="A serene Japanese garden with cherry blossoms",
    model="dall-e-3",
    size="1024x1024",
    quality="standard",
    n=1
)

# Get image URL
image_url = response['data'][0]['url']
print(f"Image generated: {image_url}")

# Check credits
metadata = response['_metadata']
print(f"Cost: {metadata['cost_incurred']} credits")
print(f"Remaining: {metadata['credits_remaining']} credits")
```

### JavaScript/TypeScript (Node.js)

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://unicorncommander.ai/api/v1/llm',
  apiKey: 'your-uc-api-key',
});

async function generateImage() {
  const response = await client.images.generate({
    prompt: 'A cyberpunk street scene at night with neon lights',
    model: 'dall-e-3',
    size: '1024x1024',
    quality: 'hd',
    n: 1,
  });

  const imageUrl = response.data[0].url;
  console.log('Image generated:', imageUrl);

  // @ts-ignore - Custom metadata field
  const metadata = response._metadata;
  console.log(`Cost: ${metadata.cost_incurred} credits`);
  console.log(`Remaining: ${metadata.credits_remaining} credits`);
}

generateImage();
```

### JavaScript (Browser/React)

```javascript
import React, { useState } from 'react';

function ImageGenerator() {
  const [prompt, setPrompt] = useState('');
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateImage = async () => {
    setLoading(true);
    try {
      const response = await fetch('https://unicorncommander.ai/api/v1/llm/image/generations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.REACT_APP_UC_API_KEY}`,
        },
        body: JSON.stringify({
          prompt,
          model: 'dall-e-3',
          size: '1024x1024',
          quality: 'standard',
        }),
      });

      const data = await response.json();
      setImageUrl(data.data[0].url);

      console.log(`Cost: ${data._metadata.cost_incurred} credits`);
    } catch (error) {
      console.error('Image generation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe your image..."
      />
      <button onClick={generateImage} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Image'}
      </button>
      {imageUrl && <img src={imageUrl} alt="Generated" />}
    </div>
  );
}
```

### cURL Examples

#### Basic DALL-E 3 Image

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer sk-uc-abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A majestic mountain landscape at sunrise",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard"
  }'
```

#### HD Landscape Image

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer sk-uc-abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A detailed architectural rendering of a modern skyscraper",
    "model": "dall-e-3",
    "size": "1792x1024",
    "quality": "hd",
    "style": "vivid"
  }'
```

#### Batch Stable Diffusion Images

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer sk-uc-abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Fantasy dragon flying over castle, multiple variations",
    "model": "stable-diffusion-xl",
    "size": "1024x1024",
    "n": 4
  }'
```

#### Base64 Response Format

```bash
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer sk-uc-abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A simple icon of a rocket ship",
    "model": "dall-e-2",
    "size": "256x256",
    "response_format": "b64_json"
  }'
```

---

## Error Handling

### Common Error Codes

| Status Code | Error | Description | Solution |
|------------|-------|-------------|----------|
| **400** | Bad Request | Invalid request parameters | Check prompt length, size format, n value |
| **401** | Unauthorized | Missing or invalid API key | Verify Authorization header |
| **402** | Payment Required | Insufficient credits | Purchase more credits or enable BYOK |
| **403** | Forbidden | Account suspended or tier limit | Contact support |
| **429** | Too Many Requests | Rate limit exceeded or monthly cap reached | Reduce request rate or upgrade tier |
| **503** | Service Unavailable | No provider configured | Contact admin to configure providers |
| **500** | Internal Server Error | Server-side error | Retry request, contact support if persists |

### Error Response Format

```json
{
  "detail": "Insufficient credits. Balance: 10.5, Estimated cost: 40.0 credits"
}
```

### Handling Errors in Code

```python
import openai

try:
    response = openai.Image.create(
        prompt="A beautiful sunset",
        model="dall-e-3"
    )
except openai.error.AuthenticationError:
    print("Invalid API key")
except openai.error.RateLimitError:
    print("Rate limit exceeded - please wait")
except openai.error.InvalidRequestError as e:
    print(f"Invalid request: {e}")
except openai.error.APIError as e:
    print(f"API error: {e}")
```

---

## Rate Limits

### By Subscription Tier

| Tier | Images/Minute | Images/Hour | Images/Day | Monthly Cap |
|------|--------------|-------------|-----------|-------------|
| **Free** | 2 | 10 | 50 | 200 images |
| **Starter** | 5 | 50 | 200 | 1,000 images |
| **Professional** | 10 | 100 | 500 | 5,000 images |
| **Enterprise** | 20 | 200 | 2,000 | Unlimited |
| **BYOK** | Unlimited* | Unlimited* | Unlimited* | Unlimited* |

*BYOK users are limited only by their provider's rate limits

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1699123500
```

### Handling Rate Limits

```python
import time

def generate_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return openai.Image.create(prompt=prompt, model="dall-e-3")
        except openai.error.RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

---

## Best Practices

### 1. Cost Optimization

✅ **Use Stable Diffusion for iteration** - Experiment with cheap SDXL, finalize with DALL-E 3
✅ **Start with standard quality** - Only use HD when truly needed
✅ **Enable BYOK for high volume** - If generating 100+ images/month
✅ **Cache results** - Store generated images to avoid re-generating

### 2. Prompt Engineering

✅ **Be specific** - "Photorealistic portrait of..." vs "A person"
✅ **Include style** - "Oil painting", "3D render", "Minimalist logo"
✅ **Specify composition** - "Centered", "bird's eye view", "close-up"
✅ **Test and iterate** - Start cheap (SDXL), refine prompt, then use DALL-E 3

### 3. Error Handling

✅ **Implement retries** - Exponential backoff for rate limits
✅ **Monitor credits** - Check balance before batch operations
✅ **Validate inputs** - Check prompt length and parameters before API call
✅ **Log metadata** - Track `transaction_id` for billing reconciliation

### 4. Security

✅ **Never expose API keys** - Use environment variables
✅ **Use server-side calls** - Don't call API from browser (except with session auth)
✅ **Validate user input** - Sanitize prompts to prevent injection
✅ **Rate limit your app** - Add your own rate limiting to prevent abuse

---

## FAQ

### Q: Can I use this API with the official OpenAI Python library?

**A:** Yes! Just change the `api_base`:

```python
import openai
openai.api_base = "https://unicorncommander.ai/api/v1/llm"
openai.api_key = "your-uc-api-key"
```

### Q: What happens if I run out of credits?

**A:** You'll get a `402 Payment Required` error. Purchase more credits or enable BYOK to continue.

### Q: Can I generate NSFW images?

**A:** No. All providers (OpenAI, OpenRouter, Stable Diffusion hosts) have content policies that block NSFW prompts.

### Q: How long are image URLs valid?

**A:** OpenAI image URLs expire after **1 hour**. Download and store images if you need them longer. Alternatively, use `response_format: "b64_json"` to get base64 data.

### Q: Can I use custom Stable Diffusion models?

**A:** Yes, with BYOK. Configure a Replicate or OpenRouter BYOK key and specify the model ID in the `model` parameter.

### Q: How do I get a refund if image quality is poor?

**A:** We don't offer refunds for generated images, as provider costs are immediate. Use Stable Diffusion for testing (2-5 credits) before using DALL-E 3.

---

## Support

**Documentation**: https://docs.unicorncommander.ai
**API Status**: https://status.unicorncommander.ai
**Community**: https://discord.gg/unicorncommander
**Email**: support@unicorncommander.ai

---

## Changelog

### v1.0.0 (2025-11-04)

- ✅ Initial release of Image Generation API
- ✅ DALL-E 2/3 support
- ✅ Stable Diffusion XL/3 support
- ✅ BYOK functionality
- ✅ Credit tracking and billing
- ✅ OpenAI SDK compatibility
- ✅ Rate limiting by tier
- ✅ Usage metering and analytics

---

**Built with ❤️ by the Unicorn Commander team**
