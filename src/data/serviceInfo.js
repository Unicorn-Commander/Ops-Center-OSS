/**
 * Service Information Data
 * Used by AIModelManagement and other service-related pages
 */

export const serviceInfo = {
  vllm: {
    name: 'vLLM',
    displayName: 'vLLM Inference Engine',
    description: 'High-performance LLM inference server optimized for NVIDIA GPUs with PagedAttention',
    port: 8000,
    url: 'http://localhost:8000',
    healthEndpoint: '/health',
    apiEndpoint: '/v1',
    status: 'operational',
    features: [
      'GPU-accelerated inference',
      'PagedAttention for efficient memory',
      'Continuous batching',
      'Streaming support',
      'OpenAI-compatible API'
    ],
    compatibleModels: 'LLaMA, Mistral, Qwen, Mixtral, Phi, Gemma, and 50+ models',
    homepage: 'https://vllm.ai',
    github: 'https://github.com/vllm-project/vllm',
    docs: 'https://docs.vllm.ai',
    defaultFilters: {
      architecture: ['decoder-only'],
      quantization: ['AWQ', 'GPTQ', 'SqueezeLLM']
    }
  },
  ollama: {
    name: 'Ollama',
    displayName: 'Ollama Local LLM',
    description: 'Run large language models locally with ease',
    port: 11434,
    url: 'http://localhost:11434',
    healthEndpoint: '/api/tags',
    apiEndpoint: '/api',
    status: 'optional',
    features: [
      'Easy model management',
      'CPU and GPU support',
      'Built-in quantization',
      'Model library',
      'Fast inference'
    ],
    compatibleModels: 'LLaMA, Mistral, CodeLLaMA, Vicuna, and custom models',
    homepage: 'https://ollama.ai',
    github: 'https://github.com/ollama/ollama',
    docs: 'https://github.com/ollama/ollama/blob/main/README.md',
    defaultFilters: {
      quantization: ['Q4_0', 'Q4_1', 'Q5_0', 'Q5_1', 'Q8_0']
    }
  },
  localai: {
    name: 'LocalAI',
    displayName: 'LocalAI',
    description: 'OpenAI-compatible API for running LLMs locally',
    port: 8080,
    url: 'http://localhost:8080',
    healthEndpoint: '/health',
    apiEndpoint: '/v1',
    status: 'optional',
    features: [
      'OpenAI API compatible',
      'Multiple model backends',
      'Text and image generation',
      'Audio transcription',
      'Embeddings support'
    ],
    compatibleModels: 'GGUF, GGML, and various model formats',
    homepage: 'https://localai.io',
    github: 'https://github.com/mudler/LocalAI',
    docs: 'https://localai.io/docs',
    defaultFilters: {}
  }
};

export const modelTips = {
  vllm: {
    installation: 'vLLM requires CUDA 11.8+ and works best with NVIDIA A100, H100, or RTX series GPUs',
    memory: 'Use GPU_MEMORY_UTIL=0.9 for optimal performance. Each model requires VRAM = model_size × 1.2',
    performance: 'Enable tensor parallelism for models >70B parameters across multiple GPUs',
    quantization: 'AWQ quantization provides the best speed/quality tradeoff for vLLM'
  },
  ollama: {
    installation: 'Ollama works on Mac, Linux, and Windows with automatic GPU detection',
    memory: 'Ollama automatically manages memory. For 7B models, 8GB RAM minimum recommended',
    performance: 'Use OLLAMA_NUM_PARALLEL for concurrent requests. Default is 1.',
    quantization: 'Q4 quantization balances size and quality. Q8 for better quality, Q2/Q3 for smaller size'
  },
  localai: {
    installation: 'LocalAI can run on CPU or GPU. Docker recommended for easiest setup',
    memory: 'Memory usage depends on model backend. GGUF models are most memory-efficient',
    performance: 'Set threads and GPU layers via model config for optimal performance',
    quantization: 'Supports GGUF quantization levels from Q2 to Q8'
  },
  general: {
    modelSelection: 'Choose models based on your use case: 7B for chat, 13B for reasoning, 70B+ for complex tasks',
    gpuMemory: 'GPU VRAM needed ≈ model params (B) × 2 bytes (FP16) or × 1 byte (INT8)',
    contextLength: 'Longer context (16K+) requires more memory. Start with 4K and increase as needed'
  }
};

export default serviceInfo;
