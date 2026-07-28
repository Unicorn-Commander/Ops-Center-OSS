import React from 'react';
import { motion } from 'framer-motion';
import { Bot, Search, MessageSquare, Code2, Mic, FileText, Terminal, LayoutDashboard } from 'lucide-react';

const features = [
  {
    icon: Bot,
    title: 'AI Chat & Agents',
    description: 'Advanced conversational AI with multi-model support',
    highlight: 'GPT-4, Claude, Gemini'
  },
  {
    icon: Search,
    title: 'Semantic Search',
    description: 'Vector search powered by cutting-edge embeddings',
    highlight: 'RAG enabled'
  },
  {
    icon: MessageSquare,
    title: 'Team Collaboration',
    description: 'Shared conversations and knowledge bases',
    highlight: 'Real-time sync'
  },
  {
    icon: Code2,
    title: 'Code Generation',
    description: 'AI-powered code completion and generation',
    highlight: '20+ languages'
  },
  {
    icon: Mic,
    title: 'Voice Services',
    description: 'Text-to-speech and speech-to-text processing',
    highlight: 'Multi-language'
  },
  {
    icon: FileText,
    title: 'Document Processing',
    description: 'Extract insights from PDFs, docs, and more',
    highlight: 'OCR included'
  },
  {
    icon: Terminal,
    title: 'API Access',
    description: 'RESTful APIs with comprehensive documentation',
    highlight: 'OpenAPI spec'
  },
  {
    icon: LayoutDashboard,
    title: 'Unified Dashboard',
    description: 'Manage all your AI tools from one place',
    highlight: 'RBAC enabled'
  }
];

export default function LandingFeatures() {
  return (
    <section className="py-24 px-4 relative bg-black/20">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Everything You Need to Build with AI
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            8 premium applications, all included in your subscription
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              className="group relative"
            >
              <div className="h-full p-6 rounded-xl bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/20 hover:scale-105">
                {/* Icon */}
                <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center mb-4 group-hover:bg-purple-500/30 transition-colors">
                  <feature.icon className="w-6 h-6 text-purple-400" />
                </div>

                {/* Content */}
                <h3 className="text-lg font-bold text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-400 mb-3">
                  {feature.description}
                </p>

                {/* Highlight */}
                <span className="text-xs font-medium text-purple-400">
                  {feature.highlight}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
