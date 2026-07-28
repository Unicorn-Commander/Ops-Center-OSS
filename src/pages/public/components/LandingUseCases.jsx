import React from 'react';
import { motion } from 'framer-motion';
import { Code, Building2, Rocket, Users } from 'lucide-react';

const useCases = [
  {
    icon: Code,
    title: 'Solo Developers',
    description: 'Build AI-powered side projects without breaking the bank. Focus on shipping, not managing API bills.',
    stats: ['Save $100+/month', 'Ship faster', 'No DevOps'],
    scenario: 'Perfect for developers building MVPs, prototypes, or side projects who want professional AI capabilities without enterprise costs.'
  },
  {
    icon: Rocket,
    title: 'Startups',
    description: 'Scale your AI features without scaling your costs. Predictable pricing as you grow from 0 to product-market fit.',
    stats: ['90% cost reduction', 'Unlimited scaling', 'Team collaboration'],
    scenario: 'Ideal for early-stage startups that need to extend their runway while shipping AI-powered features to validate product-market fit.'
  },
  {
    icon: Building2,
    title: 'Enterprises',
    description: 'Centralized AI platform for your entire organization. RBAC, SSO, compliance, and dedicated support.',
    stats: ['Enterprise SLA', 'Custom integrations', 'Dedicated support'],
    scenario: 'Built for organizations that need centralized AI infrastructure with enterprise-grade security, compliance, and vendor management.'
  },
  {
    icon: Users,
    title: 'Agencies',
    description: 'White-label AI capabilities for your clients. Manage multiple projects with unified billing and analytics.',
    stats: ['Multi-tenant', 'White-label ready', 'Client management'],
    scenario: 'Designed for agencies that want to offer AI features to multiple clients with unified billing, white-label options, and client management tools.'
  }
];

export default function LandingUseCases() {
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
            Built for Builders
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            Whether you're shipping your first AI feature or scaling to millions of users
          </p>
        </motion.div>

        {/* Use Cases Grid */}
        <div className="grid md:grid-cols-2 gap-8">
          {useCases.map((useCase, index) => (
            <motion.div
              key={useCase.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="group"
            >
              <div className="h-full p-8 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300">
                {/* Icon */}
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 p-3 mb-6 group-hover:scale-110 transition-transform">
                  <useCase.icon className="w-full h-full text-white" />
                </div>

                {/* Title & Description */}
                <h3 className="text-2xl font-bold text-white mb-3">
                  {useCase.title}
                </h3>
                <p className="text-slate-300 mb-6 leading-relaxed">
                  {useCase.description}
                </p>

                {/* Stats */}
                <div className="flex flex-wrap gap-2 mb-6">
                  {useCase.stats.map((stat) => (
                    <span
                      key={stat}
                      className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-sm font-medium"
                    >
                      {stat}
                    </span>
                  ))}
                </div>

                {/* Use Case Scenario */}
                <div className="pt-6 border-t border-white/10">
                  <p className="text-slate-400 leading-relaxed">
                    {useCase.scenario}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
