# Landing Page Configuration Templates

Ops-Center supports multiple landing page configurations for different deployment types.

## Available Templates

### 1. `landing_config.json` (Default)
**Use Case**: Generic UC-Cloud deployment with standard AI services
- Services: Open-WebUI, Center-Deep Search, vLLM, Unicorn Orator, Unicorn Amanuensis
- Branding: UC-1 Pro Operations Center
- Theme: Dashboard preset with purple/blue gradients

### 2. `landing_config.centerdeep.json`
**Use Case**: Center Deep Suite - Privacy-focused AI metasearch & B2B lead intelligence
- Services: Center Deep Pro Search, LoopNet Leads, Center Deep Intelligence
- Branding: Center Deep Online
- Theme: Professional preset with blue gradients
- Features: Pricing tiers, competitive positioning, testimonials
- Deployment: https://centerdeep.online

### 3. `landing_config.unicorncommander.json`
**Use Case**: Unicorn Commander Stack - Full AI infrastructure platform
- Services: Open-WebUI, Brigade, LLMHub, Services Dashboard
- Branding: Unicorn Commander
- Theme: Magic Unicorn preset with purple/pink gradients
- Features: Organization management, billing dashboard, admin tools
- Deployment: https://your-domain.com

## How to Use Templates

Set the `LANDING_CONFIG_TEMPLATE` environment variable:

```bash
# In .env or docker-compose.yml
LANDING_CONFIG_TEMPLATE=centerdeep
```

Or copy your desired template to `landing_config.json`:

```bash
cd backend/config/
cp landing_config.centerdeep.json landing_config.json
```

## Creating Custom Templates

1. Copy an existing template
2. Modify branding, services, theme
3. Test with `LANDING_CONFIG_TEMPLATE=mytemplate`
4. Share via pull request!

See examples in this directory for template structure.
