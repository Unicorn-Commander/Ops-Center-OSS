import React from 'react';

// Enhanced Service mappings with Function + Brand design
export const EnhancedServiceLogos = {
  vllm: {
    functionIcon: '🤖',
    functionName: 'AI Inference',
    brandLogo: (
      <div className="w-6 h-6 bg-purple-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">vL</span>
      </div>
    ),
    brandName: 'vLLM',
    color: 'bg-purple-500',
    description: 'High-performance LLM inference engine',
    hasGUI: false,
    apiPort: 8000
  },
  'open-webui': {
    functionIcon: '💬',
    functionName: 'Chat Interface',
    brandLogo: (
      <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">UI</span>
      </div>
    ),
    brandName: 'Open-WebUI',
    color: 'bg-blue-500',
    description: 'Web-based chat interface',
    hasGUI: true,
    guiPort: 8080
  },
  redis: {
    functionIcon: '⚡',
    functionName: 'Cache Store',
    brandLogo: (
      <div className="w-6 h-6 bg-red-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">R</span>
      </div>
    ),
    brandName: 'Redis',
    color: 'bg-red-500',
    description: 'In-memory data structure store',
    hasGUI: false,
    apiPort: 6379
  },
  postgresql: {
    functionIcon: '🗄️',
    functionName: 'Database',
    brandLogo: (
      <div className="w-6 h-6 bg-blue-700 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">PG</span>
      </div>
    ),
    brandName: 'PostgreSQL',
    color: 'bg-blue-600',
    description: 'Relational database system',
    hasGUI: false,
    apiPort: 5432
  },
  qdrant: {
    functionIcon: '🧮',
    functionName: 'Vector DB',
    brandLogo: (
      <div className="w-6 h-6 bg-purple-700 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">Q</span>
      </div>
    ),
    brandName: 'Qdrant',
    color: 'bg-purple-600',
    description: 'Vector similarity search engine',
    hasGUI: true,
    guiPort: 6333
  },
  whisperx: {
    functionIcon: '🎤',
    functionName: 'Speech-to-Text',
    brandLogo: (
      <div className="w-6 h-6 bg-green-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">Wx</span>
      </div>
    ),
    brandName: 'WhisperX',
    color: 'bg-green-500',
    description: 'Automatic speech recognition',
    hasGUI: false,
    apiPort: 9000
  },
  'kokoro-tts': {
    functionIcon: '🗣️',
    functionName: 'Text-to-Speech',
    brandLogo: (
      <div className="w-6 h-6 bg-pink-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">K</span>
      </div>
    ),
    brandName: 'Kokoro TTS',
    color: 'bg-pink-500',
    description: 'Neural text-to-speech synthesis',
    hasGUI: false,
    apiPort: 8880
  },
  searxng: {
    functionIcon: '🔍',
    functionName: 'AI Search',
    brandLogo: (
      <div className="w-6 h-6 bg-cyan-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">CD</span>
      </div>
    ),
    brandName: 'Center-Deep',
    color: 'bg-cyan-500',
    description: 'AI-powered search platform',
    hasGUI: true,
    guiPort: 8888
  },
  embeddings: {
    functionIcon: '📊',
    functionName: 'Embeddings',
    brandLogo: (
      <div className="w-6 h-6 bg-amber-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">Em</span>
      </div>
    ),
    brandName: 'BGE Embeddings',
    color: 'bg-amber-500',
    description: 'Text embedding generation',
    hasGUI: false,
    apiPort: 8082
  },
  reranker: {
    functionIcon: '🎯',
    functionName: 'Doc Reranking',
    brandLogo: (
      <div className="w-6 h-6 bg-cyan-700 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">Re</span>
      </div>
    ),
    brandName: 'BGE Reranker',
    color: 'bg-cyan-600',
    description: 'Document relevance reranking',
    hasGUI: false,
    apiPort: 8083
  },
  tika: {
    functionIcon: '📄',
    functionName: 'Document OCR',
    brandLogo: (
      <div className="w-6 h-6 bg-red-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">Ti</span>
      </div>
    ),
    brandName: 'Apache Tika',
    color: 'bg-red-500',
    description: 'Document processing and OCR',
    hasGUI: false,
    apiPort: 9998
  },
  'gpu-metrics': {
    functionIcon: '📈',
    functionName: 'GPU Monitor',
    brandLogo: (
      <div className="w-6 h-6 bg-lime-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">NV</span>
      </div>
    ),
    brandName: 'NVIDIA SMI',
    color: 'bg-lime-500',
    description: 'GPU performance monitoring',
    hasGUI: false,
    apiPort: 9835
  },
  brigade: {
    functionIcon: '🦄',
    functionName: 'Agent Platform',
    brandLogo: (
      <div className="w-6 h-6 bg-gradient-to-br from-purple-600 to-pink-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">🦄</span>
      </div>
    ),
    brandName: 'Unicorn Brigade',
    color: 'bg-purple-500',
    description: 'AI agent builder and orchestration',
    hasGUI: true,
    guiPort: 8102,
    externalUrl: 'https://brigade.your-domain.com'
  },
  presenton: {
    functionIcon: '📊',
    functionName: 'Presentations',
    brandLogo: (
      <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">PT</span>
      </div>
    ),
    brandName: 'PresentOn',
    color: 'bg-blue-500',
    description: 'AI-powered presentation generation',
    hasGUI: true,
    guiPort: 8091,
    externalUrl: 'https://presentations.your-domain.com'
  },
  portainer: {
    functionIcon: '🐳',
    functionName: 'Containers',
    brandLogo: (
      <div className="w-6 h-6 bg-blue-500 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">PT</span>
      </div>
    ),
    brandName: 'Portainer',
    color: 'bg-blue-400',
    description: 'Docker container management',
    hasGUI: true,
    guiPort: 9000,
    externalUrl: 'https://containers.your-domain.com'
  },
  grafana: {
    functionIcon: '📈',
    functionName: 'Monitoring',
    brandLogo: (
      <div className="w-6 h-6 bg-orange-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">Gr</span>
      </div>
    ),
    brandName: 'Grafana',
    color: 'bg-orange-500',
    description: 'Metrics visualization dashboards',
    hasGUI: true,
    guiPort: 3000
  },
  prometheus: {
    functionIcon: '📊',
    functionName: 'Metrics',
    brandLogo: (
      <div className="w-6 h-6 bg-orange-700 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">Pm</span>
      </div>
    ),
    brandName: 'Prometheus',
    color: 'bg-orange-600',
    description: 'Time-series metrics collection',
    hasGUI: true,
    guiPort: 9090
  },
  lago: {
    functionIcon: '💰',
    functionName: 'Billing',
    brandLogo: (
      <div className="w-6 h-6 bg-green-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">La</span>
      </div>
    ),
    brandName: 'Lago Billing',
    color: 'bg-green-500',
    description: 'Subscription and billing management',
    hasGUI: true,
    guiPort: 80,
    externalUrl: 'https://billing.your-domain.com'
  },
  litellm: {
    functionIcon: '🔌',
    functionName: 'LLM Proxy',
    brandLogo: (
      <div className="w-6 h-6 bg-indigo-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">LL</span>
      </div>
    ),
    brandName: 'LiteLLM',
    color: 'bg-indigo-500',
    description: 'Multi-provider LLM routing',
    hasGUI: true,
    guiPort: 4000
  },
  forgejo: {
    functionIcon: '🦊',
    functionName: 'Git Platform',
    brandLogo: (
      <div className="w-6 h-6 bg-orange-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">Fg</span>
      </div>
    ),
    brandName: 'Forgejo',
    color: 'bg-orange-500',
    description: 'Self-hosted Git platform with CI/CD',
    hasGUI: true,
    guiPort: 3000,
    externalUrl: 'https://git.your-domain.com'
  },
  woodpecker: {
    functionIcon: '🔨',
    functionName: 'CI/CD',
    brandLogo: (
      <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">WP</span>
      </div>
    ),
    brandName: 'Woodpecker CI',
    color: 'bg-blue-500',
    description: 'Continuous integration and deployment',
    hasGUI: true,
    guiPort: 8000,
    externalUrl: 'https://ci.your-domain.com'
  }
};

// Enhanced Service Card Component
export const EnhancedServiceCard = ({ serviceKey, serviceData, status, onClick, theme, currentTheme, viewMode = 'cards' }) => {
  const serviceInfo = EnhancedServiceLogos[serviceKey];
  if (!serviceInfo) return null;

  const statusColor = status === 'running' ? 'text-green-500' :
                     status === 'stopped' ? 'text-red-500' :
                     status === 'starting' ? 'text-yellow-500' : 'text-gray-500';

  const statusText = status === 'running' ? '● Online' :
                    status === 'stopped' ? '○ Offline' :
                    status === 'starting' ? '◐ Starting' : '◌ Unknown';

  // Handle clicks - open external URLs directly, show modal for others
  const handleClick = () => {
    if (serviceInfo.externalUrl) {
      window.open(serviceInfo.externalUrl, '_blank');
    } else {
      onClick({ name: serviceKey, status, ...serviceData });
    }
  };

  if (viewMode === 'circles') {
    // Circular progress view for resource usage
    const cpuUsage = serviceData?.stats?.cpu || 0;
    const circumference = 2 * Math.PI * 30; // radius 30
    const strokeDashoffset = circumference - (cpuUsage / 100) * circumference;
    
    return (
      <div
        onClick={handleClick}
        className={`${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'} rounded-lg p-4 cursor-pointer border ${
          currentTheme === 'light' ? 'border-gray-200' : 'border-gray-700'
        } hover:border-blue-500/50 transition-all`}
      >
        <div className="flex flex-col items-center gap-3">
          {/* Circular Progress */}
          <div className="relative">
            <svg className="w-16 h-16 transform -rotate-90">
              <circle
                cx="32"
                cy="32"
                r="30"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-gray-700/20"
              />
              <circle
                cx="32"
                cy="32"
                r="30"
                stroke={cpuUsage > 80 ? '#ef4444' : cpuUsage > 60 ? '#f59e0b' : '#10b981'}
                strokeWidth="4"
                fill="none"
                strokeLinecap="round"
                style={{
                  strokeDasharray: circumference,
                  strokeDashoffset: strokeDashoffset
                }}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-2xl">{serviceInfo.functionIcon}</div>
            </div>
          </div>
          
          <div className="text-center">
            <div className={`text-xs font-semibold ${theme.text.accent}`}>{serviceInfo.functionName}</div>
            <div className={`text-xs ${theme.text.secondary}`}>{serviceInfo.brandName}</div>
            <div className={`text-xs ${statusColor} mt-1`}>{statusText}</div>
          </div>
        </div>
      </div>
    );
  }
  
  // Default card view
  return (
    <div
      onClick={handleClick}
      className={`${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'} rounded-lg p-3 cursor-pointer border ${
        currentTheme === 'light' ? 'border-gray-200' : 'border-gray-700'
      } hover:border-blue-500/50 transition-all ${serviceInfo.externalUrl ? 'hover:shadow-lg' : ''}`}
    >
      <div className="flex flex-col gap-2 relative">
        {/* External link indicator */}
        {serviceInfo.externalUrl && (
          <div className="absolute -top-1 -right-1 text-xs">🔗</div>
        )}

        {/* Function + Brand Row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{serviceInfo.functionIcon}</span>
            <span className={`text-xs font-semibold ${theme.text.accent}`}>
              {serviceInfo.functionName}
            </span>
          </div>
          {serviceInfo.brandLogo}
        </div>

        {/* Brand Name */}
        <div className={`text-xs ${theme.text.secondary} text-center`}>
          {serviceInfo.brandName}
        </div>

        {/* Status */}
        <div className={`text-xs font-semibold ${statusColor} text-center`}>
          {statusText}
        </div>
      </div>
    </div>
  );
};

// Get service info with fallback
export const getEnhancedServiceInfo = (serviceName) => {
  // Try exact match first
  if (EnhancedServiceLogos[serviceName]) {
    return EnhancedServiceLogos[serviceName];
  }
  
  // Try to find partial match
  const key = Object.keys(EnhancedServiceLogos).find(k => 
    serviceName.toLowerCase().includes(k.toLowerCase()) ||
    k.toLowerCase().includes(serviceName.toLowerCase())
  );
  
  if (key) {
    return EnhancedServiceLogos[key];
  }
  
  // Return default
  return {
    functionIcon: '❓',
    functionName: 'Unknown Service',
    brandLogo: (
      <div className="w-6 h-6 bg-gray-500 rounded flex items-center justify-center">
        <span className="text-white text-xs font-bold">?</span>
      </div>
    ),
    brandName: serviceName,
    color: 'bg-gray-500',
    description: 'Unknown service',
    hasGUI: false
  };
};