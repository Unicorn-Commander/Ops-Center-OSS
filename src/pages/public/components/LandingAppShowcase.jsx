import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ExternalLink, Star } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function LandingAppShowcase() {
  const [apps, setApps] = useState([]);

  useEffect(() => {
    // Fetch apps from API
    fetch('/api/v1/apps/list')
      .then(res => res.json())
      .then(data => setApps(data.apps || []))
      .catch(err => console.error('Failed to load apps:', err));
  }, []);

  return (
    <section id="apps" className="py-24 px-4 relative" aria-labelledby="apps-heading">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 id="apps-heading" className="text-4xl md:text-5xl font-bold text-white mb-4">
            8 Premium Apps, One Subscription
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            Everything you need to build, ship, and scale AI-powered applications
          </p>
        </motion.div>

        {/* Apps Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12" role="list" aria-label="Available applications">
          {apps.slice(0, 8).map((app, index) => (
            <motion.div
              key={app.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              className="group"
              role="listitem"
            >
              <div
                className="block h-full p-6 rounded-xl bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/20 hover:scale-105"
                aria-label={`${app.name} - ${app.tagline}`}
              >
                {/* App Icon */}
                {app.icon_url ? (
                  <img
                    src={app.icon_url}
                    alt=""
                    className="w-16 h-16 rounded-lg mb-4 object-cover"
                    aria-hidden="true"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 mb-4 flex items-center justify-center" aria-hidden="true">
                    <span className="text-2xl font-bold text-white">
                      {app.name.charAt(0)}
                    </span>
                  </div>
                )}

                {/* App Info */}
                <h3 className="text-xl font-bold text-white mb-2 group-hover:text-purple-400 transition-colors">
                  {app.name}
                </h3>
                <p className="text-sm text-slate-400 mb-4 line-clamp-2">
                  {app.tagline}
                </p>

                {/* Category */}
                <span className="inline-block px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs font-medium">
                  {app.category}
                </span>

                {/* Featured Badge */}
                {app.featured && (
                  <div className="absolute top-4 right-4" role="img" aria-label="Featured app">
                    <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" aria-hidden="true" />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* View All Apps CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-center"
        >
          <Link
            to="/auth/login"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl backdrop-blur-sm border border-white/20 transition-all duration-300"
            aria-label="Sign in to explore all available apps"
          >
            <span>Get Started</span>
            <ExternalLink className="w-5 h-5" aria-hidden="true" />
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
