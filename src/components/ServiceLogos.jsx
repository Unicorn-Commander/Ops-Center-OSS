import React from 'react';

// Service logo mappings with proper brand colors
export const ServiceLogos = {
  vllm: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
        <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" className="text-purple-500"/>
        <text x="12" y="16" textAnchor="middle" className="text-white text-xs font-bold" fill="white">AI</text>
      </svg>
    ),
    color: 'bg-purple-500',
    name: 'vLLM Engine',
    description: 'High-performance LLM inference',
    hasGUI: false,
    apiPort: 8000
  },
  'open-webui': {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none">
        <rect x="3" y="3" width="18" height="18" rx="2" className="stroke-blue-500" strokeWidth="2"/>
        <path d="M8 12h8M12 8v8" className="stroke-blue-500" strokeWidth="2" strokeLinecap="round"/>
      </svg>
    ),
    color: 'bg-blue-500',
    name: 'Open WebUI',
    description: 'Chat interface',
    hasGUI: true,
    guiPort: 8080
  },
  redis: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <path d="M23.99 9.87c0-.57-2.3-1.12-5.77-1.53.31-.47.58-.95.8-1.44.98-2.16.67-3.9-.69-4.63-.43-.23-.93-.34-1.48-.34-1.64 0-3.68 1.08-5.85 2.91-2.17-1.83-4.21-2.91-5.85-2.91-.55 0-1.05.11-1.48.34-1.36.73-1.67 2.47-.69 4.63.22.49.49.97.8 1.44C.71 8.75-1.59 9.3-1.59 9.87s2.3 1.12 5.77 1.53c-.31.47-.58.95-.8 1.44-.98 2.16-.67 3.9.69 4.63.43.23.93.34 1.48.34 1.64 0 3.68-1.08 5.85-2.91 2.17 1.83 4.21 2.91 5.85 2.91.55 0 1.05-.11 1.48-.34 1.36-.73 1.67-2.47.69-4.63-.22-.49-.49-.97-.8-1.44 3.47-.41 5.77-.96 5.77-1.53z" fill="#DC382D"/>
      </svg>
    ),
    color: 'bg-red-500',
    name: 'Redis',
    description: 'In-memory cache',
    hasGUI: false,
    apiPort: 6379
  },
  postgresql: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <path d="M17.128 0a10.134 10.134 0 00-2.755.403l-.063.02A10.922 10.922 0 0012.021 0C8.976 0 6.472 1.686 5.07 4.312a8.822 8.822 0 00-1.503 4.994c.03 2.852 1.069 5.397 2.917 7.164l.004.003c1.853 1.77 4.274 2.744 6.82 2.744 2.39 0 4.687-.86 6.465-2.42l.003-.003c1.778-1.56 2.757-3.658 2.757-5.907 0-2.087-.843-4.019-2.373-5.44l-.003-.003C18.627.884 16.98 0 15.16 0c-.677 0-1.34.123-1.968.362l-.064.026z" fill="#4169E1"/>
      </svg>
    ),
    color: 'bg-blue-600',
    name: 'PostgreSQL',
    description: 'Relational database',
    hasGUI: false,
    apiPort: 5432
  },
  qdrant: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <circle cx="12" cy="12" r="10" fill="#7C3AED"/>
        <text x="12" y="16" textAnchor="middle" className="text-white text-xs font-bold" fill="white">Q</text>
      </svg>
    ),
    color: 'bg-purple-600',
    name: 'Qdrant',
    description: 'Vector database',
    hasGUI: true,
    guiPort: 6333
  },
  whisperx: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <path d="M12 15c1.66 0 3-1.34 3-3V6c0-1.66-1.34-3-3-3S9 4.34 9 6v6c0 1.66 1.34 3 3 3z" fill="#10B981"/>
        <path d="M17 12c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V22h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" fill="#10B981"/>
      </svg>
    ),
    color: 'bg-green-500',
    name: 'WhisperX',
    description: 'Speech-to-text',
    hasGUI: false,
    apiPort: 9000
  },
  'kokoro-tts': {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <path d="M9 9v6h4l5 5V4l-5 5H9z" fill="#EC4899"/>
        <path d="M5 9v6h2V9H5z" fill="#EC4899"/>
      </svg>
    ),
    color: 'bg-pink-500',
    name: 'Kokoro TTS',
    description: 'Text-to-speech',
    hasGUI: false,
    apiPort: 8880
  },
  searxng: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <circle cx="11" cy="11" r="8" fill="none" stroke="#0EA5E9" strokeWidth="2"/>
        <path d="M21 21l-4.35-4.35" stroke="#0EA5E9" strokeWidth="2" strokeLinecap="round"/>
        <text x="11" y="14" textAnchor="middle" className="text-xs font-bold" fill="#0EA5E9">CD</text>
      </svg>
    ),
    color: 'bg-cyan-500',
    name: 'Center-Deep',
    description: 'AI search platform',
    hasGUI: true,
    guiPort: 8888
  },
  embeddings: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <rect x="3" y="3" width="7" height="7" fill="#F59E0B"/>
        <rect x="14" y="3" width="7" height="7" fill="#F59E0B"/>
        <rect x="3" y="14" width="7" height="7" fill="#F59E0B"/>
        <rect x="14" y="14" width="7" height="7" fill="#F59E0B"/>
        <path d="M10 10h4v4h-4z" fill="#F59E0B" opacity="0.5"/>
      </svg>
    ),
    color: 'bg-amber-500',
    name: 'Embeddings',
    description: 'Text embeddings',
    hasGUI: false,
    apiPort: 8082
  },
  reranker: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <path d="M3 3h18v2H3zm0 4h12v2H3zm0 4h18v2H3zm0 4h8v2H3zm0 4h14v2H3z" fill="#06B6D4"/>
      </svg>
    ),
    color: 'bg-cyan-600',
    name: 'Reranker',
    description: 'Document reranking',
    hasGUI: false,
    apiPort: 8083
  },
  tika: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6z" fill="#EF4444"/>
        <path d="M14 2v6h6" fill="#EF4444" opacity="0.7"/>
        <text x="12" y="16" textAnchor="middle" className="text-white text-xs font-bold" fill="white">OCR</text>
      </svg>
    ),
    color: 'bg-red-500',
    name: 'Apache Tika',
    description: 'Document processing',
    hasGUI: false,
    apiPort: 9998
  },
  'gpu-metrics': {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <rect x="4" y="8" width="16" height="8" rx="1" fill="#84CC16" stroke="#84CC16" strokeWidth="2"/>
        <circle cx="8" cy="12" r="1" fill="white"/>
        <circle cx="12" cy="12" r="1" fill="white"/>
        <circle cx="16" cy="12" r="1" fill="white"/>
      </svg>
    ),
    color: 'bg-lime-500',
    name: 'GPU Metrics',
    description: 'NVIDIA monitoring',
    hasGUI: false,
    apiPort: 9835
  },
  prometheus: {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 22.5c-5.799 0-10.5-4.701-10.5-10.5S6.201 1.5 12 1.5s10.5 4.701 10.5 10.5-4.701 10.5-10.5 10.5z" fill="#E6522C"/>
        <path d="M12 6.75a5.25 5.25 0 100 10.5 5.25 5.25 0 000-10.5z" fill="#E6522C"/>
      </svg>
    ),
    color: 'bg-orange-500',
    name: 'Prometheus',
    description: 'Metrics collection',
    hasGUI: true,
    guiPort: 9090
  }
};

// Get service info with fallback
export const getServiceInfo = (serviceName) => {
  // Try exact match first
  if (ServiceLogos[serviceName]) {
    return ServiceLogos[serviceName];
  }
  
  // Try to find partial match
  const key = Object.keys(ServiceLogos).find(k => 
    serviceName.toLowerCase().includes(k.toLowerCase()) ||
    k.toLowerCase().includes(serviceName.toLowerCase())
  );
  
  if (key) {
    return ServiceLogos[key];
  }
  
  // Return default
  return {
    logo: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <rect x="4" y="4" width="16" height="16" rx="2" fill="currentColor" className="text-gray-500"/>
        <text x="12" y="16" textAnchor="middle" className="text-white text-xs font-bold" fill="white">?</text>
      </svg>
    ),
    color: 'bg-gray-500',
    name: serviceName,
    description: 'Service',
    hasGUI: false
  };
};