import React from 'react';
import { motion } from 'framer-motion';
import { DollarSign, Gauge, Lock, Zap, Code, Users } from 'lucide-react';

const benefits = [
  {
    icon: DollarSign,
    title: 'Save 90%+ on AI Costs',
    description: 'Stop paying $0.03 per 1K tokens. Get unlimited access to GPT-4, Claude, and more for one flat monthly rate.',
    stat: '$50/mo vs $5,000/mo',
    color: 'from-green-400 to-emerald-600'
  },
  {
    icon: Gauge,
    title: 'Predictable Billing',
    description: 'No more surprise bills. No usage limits. No rate limiting. Build confidently knowing your costs are fixed.',
    stat: '100% predictable',
    color: 'from-blue-400 to-cyan-600'
  },
  {
    icon: Lock,
    title: 'Bring Your Own Keys (BYOK)',
    description: 'Use your own API keys for maximum control and privacy, or let us manage everything for you.',
    stat: 'Full control',
    color: 'from-purple-400 to-pink-600'
  },
  {
    icon: Zap,
    title: 'Lightning Fast Setup',
    description: 'From signup to first API call in under 60 seconds. No complex integrations. No DevOps required.',
    stat: '< 60 seconds',
    color: 'from-yellow-400 to-orange-600'
  },
  {
    icon: Code,
    title: 'Developer-First Platform',
    description: 'Built by developers, for developers. Clean APIs, comprehensive docs, and powerful SDKs.',
    stat: 'REST + SDKs',
    color: 'from-indigo-400 to-purple-600'
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Manage your entire team with role-based access control, shared resources, and unified billing.',
    stat: 'Unlimited seats',
    color: 'from-pink-400 to-rose-600'
  }
];

export default function LandingBenefits() {
  return (
    <section className="py-24 px-4 relative">
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
            Why Developers Choose UC-Cloud
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            Stop managing multiple API subscriptions. Get everything you need in one powerful platform.
          </p>
        </motion.div>

        {/* Benefits Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {benefits.map((benefit, index) => (
            <motion.div
              key={benefit.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="group relative"
            >
              <div className="h-full p-8 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/20">
                {/* Icon */}
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${benefit.color} p-3 mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <benefit.icon className="w-full h-full text-white" />
                </div>

                {/* Content */}
                <h3 className="text-2xl font-bold text-white mb-3">
                  {benefit.title}
                </h3>
                <p className="text-slate-300 mb-4 leading-relaxed">
                  {benefit.description}
                </p>

                {/* Stat */}
                <div className={`inline-block px-4 py-2 rounded-lg bg-gradient-to-r ${benefit.color} bg-opacity-10 border border-current`}>
                  <span className={`text-sm font-semibold bg-gradient-to-r ${benefit.color} bg-clip-text text-transparent`}>
                    {benefit.stat}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
