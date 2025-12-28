import React from 'react';
import { motion } from 'framer-motion';
import { Rocket, ArrowRight, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function LandingFinalCTA() {
  return (
    <section className="py-24 px-4 relative overflow-hidden" aria-labelledby="cta-heading">
      {/* Background Effects */}
      <div className="absolute inset-0" aria-hidden="true">
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-purple-500/20 rounded-full blur-3xl animate-pulse" />
      </div>

      <div className="max-w-5xl mx-auto relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center p-12 md:p-16 rounded-3xl bg-gradient-to-br from-purple-600/20 to-pink-600/20 backdrop-blur-sm border border-purple-500/30 shadow-2xl shadow-purple-500/20"
        >
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/20 border border-purple-500/30 mb-6" role="status">
            <Sparkles className="w-4 h-4 text-purple-400" aria-hidden="true" />
            <span className="text-sm font-medium text-purple-300">
              7-Day Free Trial • No Credit Card Required
            </span>
          </div>

          {/* Headline */}
          <h2 id="cta-heading" className="text-4xl md:text-6xl font-bold text-white mb-6">
            Ready to Stop Paying
            <br />
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Per Token?
            </span>
          </h2>

          {/* Description */}
          <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
            Join thousands of developers who've already made the switch to predictable AI costs.
            Start building today.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8">
            <Link
              to="/auth/login"
              className="group px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold rounded-xl shadow-lg shadow-purple-500/50 hover:shadow-purple-500/80 transition-all duration-300 flex items-center gap-2 text-lg"
              aria-label="Start your 7-day free trial - no credit card required"
            >
              <span>Start Free Trial</span>
              <Rocket className="w-5 h-5 group-hover:translate-x-1 transition-transform" aria-hidden="true" />
            </Link>

            <a
              href="#apps"
              className="group px-8 py-4 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl backdrop-blur-sm border border-white/20 transition-all duration-300 flex items-center gap-2"
              aria-label="Explore all available applications"
            >
              <span>Explore Apps</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" aria-hidden="true" />
            </a>
          </div>

          {/* Trust Signals */}
          <div className="flex flex-wrap items-center justify-center gap-8 text-sm text-slate-400" role="list" aria-label="Trust signals">
            <div className="flex items-center gap-2" role="listitem">
              <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2" role="listitem">
              <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Cancel anytime</span>
            </div>
            <div className="flex items-center gap-2" role="listitem">
              <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Setup in 60 seconds</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
