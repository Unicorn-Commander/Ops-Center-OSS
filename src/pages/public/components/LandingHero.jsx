import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Zap, Shield, Rocket } from 'lucide-react';

export default function LandingHero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-4 py-20" aria-labelledby="hero-heading">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative max-w-7xl mx-auto text-center z-10">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 backdrop-blur-sm mb-8"
          role="status"
          aria-label="Product category badge"
        >
          <Sparkles className="w-4 h-4 text-purple-400" aria-hidden="true" />
          <span className="text-sm font-medium text-purple-300">
            The AI Command Center for Developers
          </span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          id="hero-heading"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400"
        >
          Stop Paying Per Token
          <br />
          <span className="text-white">Start Building</span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-xl md:text-2xl text-slate-300 mb-12 max-w-4xl mx-auto leading-relaxed"
        >
          One flat-rate subscription. Unlimited access to <span className="text-purple-400 font-semibold">8 premium AI apps</span>.
          <br />
          No usage limits. No surprise bills. Just pure AI power.
        </motion.p>

        {/* Value Props */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-wrap items-center justify-center gap-6 mb-12"
          role="list"
          aria-label="Key benefits"
        >
          <div className="flex items-center gap-2 text-slate-300" role="listitem">
            <Zap className="w-5 h-5 text-yellow-400" aria-hidden="true" />
            <span>Save 90%+ on AI costs</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300" role="listitem">
            <Shield className="w-5 h-5 text-green-400" aria-hidden="true" />
            <span>BYOK or managed</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300" role="listitem">
            <Rocket className="w-5 h-5 text-blue-400" aria-hidden="true" />
            <span>Ship faster</span>
          </div>
        </motion.div>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            to="/auth/login"
            className="group px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold rounded-xl shadow-lg shadow-purple-500/50 hover:shadow-purple-500/80 transition-all duration-300 flex items-center gap-2"
            aria-label="Start your free trial - sign in to get started"
          >
            <span>Start Free Trial</span>
            <Rocket className="w-5 h-5 group-hover:translate-x-1 transition-transform" aria-hidden="true" />
          </Link>

          <a
            href="#apps"
            className="px-8 py-4 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl backdrop-blur-sm border border-white/20 transition-all duration-300"
            aria-label="Explore all available apps"
          >
            Explore Apps
          </a>
        </motion.div>

        {/* Social Proof */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-16 text-slate-400 text-sm"
        >
          Trusted by developers and startups worldwide
        </motion.div>
      </div>
    </section>
  );
}
