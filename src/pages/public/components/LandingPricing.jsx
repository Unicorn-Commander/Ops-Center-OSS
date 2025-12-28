import React from 'react';
import { motion } from 'framer-motion';
import { Check, X, Zap, Rocket } from 'lucide-react';
import { Link } from 'react-router-dom';

const tiers = [
  {
    name: 'BYOK',
    price: '$30',
    period: '/month',
    description: 'Bring your own API keys',
    icon: Zap,
    color: 'from-blue-400 to-cyan-500',
    popular: true,
    features: [
      '7 Premium Apps',
      'Use Your Own API Keys',
      'Unlimited Usage (your keys)',
      'Priority Support',
      'Team Collaboration',
      'Advanced Analytics'
    ],
    limitations: [],
    cta: 'Start Free Trial',
    ctaLink: '/auth/login'
  },
  {
    name: 'Managed',
    price: '$50',
    period: '/month',
    description: 'We handle everything',
    icon: Rocket,
    color: 'from-purple-400 to-pink-500',
    features: [
      'All 8 Apps',
      'Fully Managed APIs',
      'Unlimited API Calls',
      '24/7 Support',
      'Custom Integrations',
      'SLA Guarantee',
      'Dedicated Account Manager'
    ],
    limitations: [],
    cta: 'Start Free Trial',
    ctaLink: '/auth/login'
  }
];

export default function LandingPricing() {
  return (
    <section className="py-24 px-4 relative bg-black/20" aria-labelledby="pricing-heading">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 id="pricing-heading" className="text-4xl md:text-5xl font-bold text-white mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            Choose the plan that works for you. No hidden fees. Cancel anytime.
          </p>
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-2 gap-8 mb-16 max-w-5xl mx-auto" role="list" aria-label="Pricing plans">
          {tiers.map((tier, index) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className={`relative ${tier.popular ? 'md:-mt-4 md:mb-4' : ''}`}
              role="listitem"
            >
              {/* Popular Badge */}
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-10" role="status" aria-label="Most popular plan">
                  <span className={`px-4 py-1 rounded-full bg-gradient-to-r ${tier.color} text-white text-sm font-bold shadow-lg`}>
                    Most Popular
                  </span>
                </div>
              )}

              <div className={`h-full p-8 rounded-2xl backdrop-blur-sm border ${
                tier.popular
                  ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20 border-purple-500/50 shadow-2xl shadow-purple-500/30'
                  : 'bg-white/5 border-white/10'
              } transition-all duration-300 hover:scale-105`}
              role="article"
              aria-labelledby={`tier-${tier.name}`}>
                {/* Icon */}
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${tier.color} p-3 mb-6`} aria-hidden="true">
                  <tier.icon className="w-full h-full text-white" />
                </div>

                {/* Plan Name */}
                <h3 id={`tier-${tier.name}`} className="text-2xl font-bold text-white mb-2">
                  {tier.name}
                </h3>
                <p className="text-slate-400 mb-6">
                  {tier.description}
                </p>

                {/* Price */}
                <div className="mb-8" aria-label={`Price: ${tier.price} per month`}>
                  <span className="text-5xl font-bold text-white">{tier.price}</span>
                  <span className="text-slate-400">{tier.period}</span>
                </div>

                {/* CTA Button */}
                <Link
                  to={tier.ctaLink}
                  className={`block w-full py-3 px-6 rounded-xl font-semibold text-center mb-8 transition-all duration-300 ${
                    tier.popular
                      ? `bg-gradient-to-r ${tier.color} text-white hover:shadow-lg hover:shadow-purple-500/50`
                      : 'bg-white/10 text-white hover:bg-white/20'
                  }`}
                  aria-label={`${tier.cta} for ${tier.name} plan at ${tier.price} per month`}
                >
                  {tier.cta}
                </Link>

                {/* Features */}
                <ul className="space-y-3" aria-label={`Features included in ${tier.name} plan`}>
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                      <span className="text-slate-300">{feature}</span>
                    </li>
                  ))}
                  {tier.limitations.map((limitation) => (
                    <li key={limitation} className="flex items-start gap-3">
                      <X className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                      <span className="text-slate-400">{limitation}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Comparison Note */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-center p-8 rounded-2xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20"
        >
          <p className="text-lg text-slate-300 mb-4">
            <span className="font-bold text-white">Save 90%+</span> compared to managing individual API subscriptions
          </p>
          <p className="text-slate-400">
            OpenAI + Anthropic + Others = <span className="line-through">$500-5,000/mo</span> → <span className="text-green-400 font-bold">$30-50/mo</span>
          </p>
        </motion.div>
      </div>
    </section>
  );
}
