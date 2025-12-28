# LiteLLM Management UI Components

React components for managing LLM models, providers, routing, and analytics.

## Components

### Model Management

#### ModelCard.jsx
Displays individual model information with status, usage, and action buttons.

**Props**:
- `model` (object): Model configuration
- `onEdit` (function): Edit handler
- `onDelete` (function): Delete handler
- `onTest` (function): Test handler

**Usage**:
```jsx
<ModelCard
  model={modelData}
  onEdit={(model) => console.log('Edit', model)}
  onDelete={(model) => console.log('Delete', model)}
  onTest={(model) => console.log('Test', model)}
/>
```

#### ModelRegistry.jsx
Main component for model registry with filtering and CRUD operations.

**Props**:
- `showSnackbar` (function): Snackbar notification function

**Features**:
- Search models by name/ID
- Filter by provider and status
- Add new models
- Edit/delete existing models
- Test models with prompts

**Usage**:
```jsx
<ModelRegistry showSnackbar={showSnackbar} />
```

#### ModelAddModal.jsx
Modal dialog for adding new models to the registry.

**Props**:
- `open` (boolean): Dialog open state
- `onClose` (function): Close handler
- `onAdd` (function): Add model handler (async)

**Usage**:
```jsx
<ModelAddModal
  open={isOpen}
  onClose={() => setIsOpen(false)}
  onAdd={async (modelData) => {
    // Add model via API
    await fetch('/api/v1/llm/models', {
      method: 'POST',
      body: JSON.stringify(modelData)
    });
  }}
/>
```

#### ModelTestModal.jsx
Modal for testing models with custom prompts.

**Props**:
- `open` (boolean): Dialog open state
- `model` (object): Model to test
- `onClose` (function): Close handler
- `onTest` (function): Test handler (async)

**Usage**:
```jsx
<ModelTestModal
  open={testOpen}
  model={selectedModel}
  onClose={() => setTestOpen(false)}
  onTest={async (modelId, prompt) => {
    const response = await fetch(`/api/v1/llm/models/${modelId}/test`, {
      method: 'POST',
      body: JSON.stringify({ test_prompt: prompt })
    });
    return await response.json();
  }}
/>
```

### Provider Management

#### ProviderCard.jsx
Displays provider information with status and actions.

**Props**:
- `provider` (object): Provider configuration
- `onEdit` (function): Edit handler
- `onDelete` (function): Delete handler
- `onTest` (function): Test connectivity handler

**Usage**:
```jsx
<ProviderCard
  provider={providerData}
  onEdit={(p) => console.log('Edit', p)}
  onDelete={(p) => console.log('Delete', p)}
  onTest={(p) => console.log('Test', p)}
/>
```

### Analytics

#### UsageChart.jsx
Bar chart displaying usage statistics by model or provider.

**Props**:
- `data` (object): Usage data (model/provider -> stats)
- `title` (string): Chart title

**Usage**:
```jsx
<UsageChart
  data={{
    'vllm:qwen2.5': { request_count: 1000, total_input_tokens: 50000 },
    'openai:gpt-4': { request_count: 500, total_input_tokens: 25000 }
  }}
  title="Usage by Model (Last 7 Days)"
/>
```

#### CostChart.jsx
Pie chart displaying cost breakdown.

**Props**:
- `data` (object): Cost data (model/provider -> cost)
- `title` (string): Chart title

**Usage**:
```jsx
<CostChart
  data={{
    'vllm:qwen2.5': { total_cost: 0.50 },
    'openai:gpt-4': { total_cost: 12.75 }
  }}
  title="Cost Breakdown (Last 30 Days)"
/>
```

### Settings

#### CacheStatsCard.jsx
Displays cache statistics with clear cache action.

**Props**:
- `stats` (object): Cache statistics
- `onClear` (function): Clear cache handler

**Usage**:
```jsx
<CacheStatsCard
  stats={{
    hit_rate: 0.75,
    total_requests: 1000,
    cache_hits: 750,
    cache_misses: 250,
    size_mb: 45.2,
    max_size_mb: 100
  }}
  onClear={async () => {
    await fetch('/api/v1/llm/cache/clear', { method: 'POST' });
  }}
/>
```

## Dependencies

All components require:
- React 18+
- Material-UI (MUI) v5+
- Recharts (for charts)

Install dependencies:
```bash
npm install @mui/material @emotion/react @emotion/styled recharts
```

## Styling

Components use MUI's theming system and respect the application's current theme (Magic Unicorn, Dark, or Light).

## API Integration

All components interact with the LiteLLM Management API at `/api/v1/llm/*`. Ensure:

1. Admin token is stored in `localStorage.getItem('adminToken')`
2. Backend server is running with litellm_api routes registered
3. CORS is configured if frontend is on different port

## Common Patterns

### Fetching Data

```jsx
const fetchModels = async () => {
  const response = await fetch('/api/v1/llm/models', {
    headers: {
      'X-Admin-Token': localStorage.getItem('adminToken') || ''
    }
  });

  if (!response.ok) {
    throw new Error('Failed to fetch models');
  }

  const data = await response.json();
  setModels(data.models || []);
};
```

### Error Handling

```jsx
try {
  await someAsyncOperation();
  showSnackbar('Success!', 'success');
} catch (err) {
  showSnackbar(err.message, 'error');
}
```

### Loading States

```jsx
const [loading, setLoading] = useState(false);

const fetchData = async () => {
  setLoading(true);
  try {
    // Fetch data
  } finally {
    setLoading(false);
  }
};

// In render
{loading ? <CircularProgress /> : <DataDisplay />}
```

## Testing

Test components with React Testing Library:

```bash
npm test src/components/llm/
```

## Future Enhancements

- [ ] Drag-and-drop routing rule priority
- [ ] Real-time usage charts
- [ ] Export analytics to CSV/PDF
- [ ] Inline model editing
- [ ] Batch model operations
- [ ] Custom chart date ranges
- [ ] Provider health indicators
- [ ] Cost projections

## Troubleshooting

### Component not rendering
Check that:
1. Component is imported correctly
2. Props are passed correctly
3. No console errors
4. Parent component is rendered

### API calls failing
Verify:
1. Admin token exists in localStorage
2. Backend server is running
3. API endpoints are registered
4. Network tab shows correct request

### Charts not displaying
Ensure:
1. Recharts is installed
2. Data format matches expected structure
3. Container has defined width/height

## Support

For issues or questions:
- Check component source code in `src/components/llm/`
- Review main page in `src/pages/LLMManagement.jsx`
- See API documentation in `backend/docs/LITELLM_MANAGEMENT.md`
