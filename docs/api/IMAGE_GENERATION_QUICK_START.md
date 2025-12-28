# What to Tell Other AI / App Developers

## Quick Summary

**Image Generation API is now live at Ops-Center!** 🎨

You can now generate images using DALL-E 2/3, Stable Diffusion, and other models through our OpenAI-compatible API endpoint.

---

## For App Developers Integration

### 1. Endpoint Information

**Base URL**: `https://your-domain.com/api/v1/llm`

**Endpoint**: `POST /image/generations`

**OpenAI SDK Compatible**: Yes! Works with official OpenAI libraries.

### 2. Quick Start (Copy-Paste Ready)

#### Python

```python
import openai

# Configure for Unicorn Commander
openai.api_base = "https://your-domain.com/api/v1/llm"
openai.api_key = "YOUR_UC_API_KEY"  # Get from ops-center

# Generate image
response = openai.Image.create(
    prompt="A majestic unicorn in a magical forest",
    model="dall-e-3",
    size="1024x1024",
    quality="standard"
)

image_url = response['data'][0]['url']
print(f"Generated: {image_url}")
print(f"Cost: {response['_metadata']['cost_incurred']} credits")
```

#### JavaScript/TypeScript

```javascript
const response = await fetch('https://your-domain.com/api/v1/llm/image/generations', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_UC_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: 'A majestic unicorn in a magical forest',
    model: 'dall-e-3',
    size: '1024x1024',
    quality: 'standard'
  })
});

const data = await response.json();
console.log('Image:', data.data[0].url);
console.log('Cost:', data._metadata.cost_incurred, 'credits');
```

#### cURL

```bash
curl -X POST https://your-domain.com/api/v1/llm/image/generations \
  -H "Authorization: Bearer YOUR_UC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A majestic unicorn in a magical forest",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard"
  }'
```

---

## 3. Supported Models

| Model | Best For | Cost (credits) | Speed |
|-------|---------|---------------|-------|
| **dall-e-3** | Highest quality, photorealistic | 40-80 | Slow |
| **dall-e-2** | Batch generation, quick iterations | 16-18 | Fast |
| **stable-diffusion-xl** | Artistic styles, low cost | 2-5 | Very Fast |
| **stable-diffusion-3** | Latest SD, better quality | 3-10 | Fast |

**Recommendation**: Use Stable Diffusion for testing/iteration (cheap), DALL-E 3 for final production images.

---

## 4. Request Parameters

### Required
- **`prompt`** (string): Description of image to generate

### Optional
- **`model`** (string): Model to use (default: `dall-e-3`)
- **`n`** (int): Number of images 1-10 (default: 1)
- **`size`** (string): Image size (default: `1024x1024`)
  - DALL-E 3: `1024x1024`, `1792x1024`, `1024x1792`
  - DALL-E 2: `256x256`, `512x512`, `1024x1024`
  - Stable Diffusion: `512x512`, `1024x1024`, `1536x1536`
- **`quality`** (string): `standard` or `hd` (DALL-E 3 only)
- **`style`** (string): `vivid` or `natural` (DALL-E 3 only)
- **`response_format`** (string): `url` or `b64_json` (default: `url`)

---

## 5. Response Format

```json
{
  "created": 1699123456,
  "data": [
    {
      "url": "https://...",
      "revised_prompt": "Enhanced prompt (DALL-E 3 only)"
    }
  ],
  "_metadata": {
    "provider_used": "OpenRouter",
    "cost_incurred": 40.0,
    "credits_remaining": 9960.0,
    "images_generated": 1,
    "size": "1024x1024",
    "quality": "standard"
  }
}
```

**Important**: Image URLs expire after 1 hour. Download and store them if needed longer.

---

## 6. Pricing & Credits

**Credit System**: 1 credit = $0.001 USD

### Tier Pricing

| Tier | Markup | Notes |
|------|--------|-------|
| **Free** | +50% | Good for testing |
| **Managed** | +20% | Platform handles billing |
| **BYOK** | 0% | Use your own API key, no credits charged |
| **VIP Founder** | 0% | No markup |

### Example Costs (Managed Tier)

- DALL-E 3 standard (1024x1024): **48 credits** (~$0.048)
- DALL-E 3 HD (1024x1024): **96 credits** (~$0.096)
- DALL-E 2 (1024x1024): **22 credits** (~$0.022)
- Stable Diffusion XL (1024x1024): **6 credits** (~$0.006)

---

## 7. BYOK (Bring Your Own Key)

### Enable BYOK to Avoid Credit Charges

If your users have their own OpenAI or OpenRouter API keys, they can add them:

```python
# Add BYOK key (one-time setup)
import requests

requests.post('https://your-domain.com/api/v1/llm/byok/keys',
    headers={'Authorization': 'Bearer UC_API_KEY'},
    json={
        'provider': 'openrouter',  # or 'openai'
        'api_key': 'sk-or-v1-...'   # User's provider key
    }
)
```

After adding BYOK:
- **No credits charged** for image generation
- Users pay provider directly
- Unlimited image generation (subject to provider limits)

---

## 8. Error Handling

### Common Errors

| Code | Error | Fix |
|------|-------|-----|
| 400 | Bad Request | Check parameters (prompt, size, n) |
| 401 | Unauthorized | Verify API key is valid |
| 402 | Payment Required | Insufficient credits - buy more or enable BYOK |
| 429 | Rate Limit | Too many requests - wait or upgrade tier |
| 503 | No Provider | Contact admin to configure OpenRouter/OpenAI |

### Example Error Response

```json
{
  "detail": "Insufficient credits. Balance: 10.5, Estimated cost: 40.0 credits"
}
```

### Retry Logic

```python
import time

def generate_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return openai.Image.create(prompt=prompt, model="dall-e-3")
        except openai.error.RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

---

## 9. Best Practices for App Developers

### ✅ Cost Optimization
1. **Use Stable Diffusion for iteration** - Test prompts cheaply before using DALL-E 3
2. **Start with standard quality** - Only use HD when needed
3. **Offer BYOK to power users** - Let users bring their own keys
4. **Cache results** - Store generated images, don't regenerate

### ✅ User Experience
1. **Show cost estimates** - Display credit cost before generation
2. **Handle failures gracefully** - Show error messages, retry automatically
3. **Download images immediately** - URLs expire in 1 hour
4. **Progress indicators** - Image generation takes 5-30 seconds

### ✅ Security
1. **Never expose API keys** - Use server-side calls only
2. **Validate user prompts** - Sanitize inputs to prevent injection
3. **Rate limit your app** - Add your own rate limiting
4. **Monitor usage** - Track `_metadata` for cost control

---

## 10. Full API Documentation

**Complete Guide**: `/tmp/IMAGE_GENERATION_API_GUIDE.md`

This includes:
- Detailed parameter documentation
- All supported models and pricing
- Code examples in 5+ languages
- Advanced use cases (batch generation, custom models)
- BYOK setup guide
- Rate limits by tier
- FAQ and troubleshooting

---

## 11. Example: React Image Generator Component

```jsx
import React, { useState } from 'react';

function ImageGenerator() {
  const [prompt, setPrompt] = useState('');
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cost, setCost] = useState(0);

  const generateImage = async () => {
    setLoading(true);
    try {
      const res = await fetch('https://your-domain.com/api/v1/llm/image/generations', {
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

      const data = await res.json();

      if (res.ok) {
        setImageUrl(data.data[0].url);
        setCost(data._metadata.cost_incurred);
      } else {
        alert(`Error: ${data.detail}`);
      }
    } catch (error) {
      console.error('Failed to generate image:', error);
      alert('Failed to generate image. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px' }}>
      <h2>Image Generator</h2>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe your image... (e.g., 'A majestic unicorn in a magical forest')"
        rows={4}
        style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
      />

      <button
        onClick={generateImage}
        disabled={loading || !prompt}
        style={{
          padding: '10px 20px',
          backgroundColor: '#6366f1',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Generating...' : 'Generate Image (40 credits)'}
      </button>

      {cost > 0 && (
        <p style={{ marginTop: '10px', color: '#666' }}>
          Cost: {cost} credits
        </p>
      )}

      {imageUrl && (
        <div style={{ marginTop: '20px' }}>
          <img
            src={imageUrl}
            alt="Generated"
            style={{ maxWidth: '100%', borderRadius: '8px' }}
          />
          <p style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
            URL expires in 1 hour - download to keep
          </p>
        </div>
      )}
    </div>
  );
}

export default ImageGenerator;
```

---

## 12. Support & Resources

- **API Endpoint**: `https://your-domain.com/api/v1/llm/image/generations`
- **Get API Key**: Log in to Ops-Center → Account → API Keys
- **Check Credits**: `GET /api/v1/llm/credits`
- **Enable BYOK**: `POST /api/v1/llm/byok/keys`
- **Documentation**: See `/tmp/IMAGE_GENERATION_API_GUIDE.md` for full details

---

## 13. Quick Comparison: Managed vs BYOK

| Feature | Managed (Pay with Credits) | BYOK (Your Own Key) |
|---------|---------------------------|---------------------|
| **Setup** | No setup needed | Add API key once |
| **Cost** | Credits + 20% markup | Provider cost only (no markup) |
| **Billing** | Monthly credit purchases | Direct provider billing |
| **Usage Limits** | Tier-based limits | Provider limits only |
| **Best For** | Low volume, convenience | High volume, cost control |

---

**That's it!** The image generation API is now live and ready for integration. Share this guide with your app developers and they'll be generating images in minutes.

**Questions?** Check the full documentation at `/tmp/IMAGE_GENERATION_API_GUIDE.md`
