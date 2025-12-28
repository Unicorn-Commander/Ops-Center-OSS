import React from 'react';
import { Link } from 'react-router-dom';
import ErrorBoundary from '../../components/ErrorBoundary';

/**
 * MarketplaceLanding - Public-facing landing page for unauthenticated users
 *
 * This is a simplified version that shows a basic landing page.
 * Full featured components (LandingHero, LandingFeatures, etc.) can be added later.
 */
export default function MarketplaceLanding() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Navigation Header */}
        <header className="fixed top-0 left-0 right-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-purple-500/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              {/* Logo */}
              <div className="flex items-center space-x-3">
                <img
                  src="/logos/The_Colonel.png"
                  alt="The Colonel - Unicorn Commander"
                  className="h-10 w-10 rounded-full"
                />
                <span className="text-xl font-bold text-white">
                  Unicorn Commander
                </span>
              </div>

              {/* Navigation Links */}
              <nav className="hidden md:flex items-center space-x-8">
                <a href="#features" className="text-gray-300 hover:text-white transition-colors">
                  Features
                </a>
                <a href="#pricing" className="text-gray-300 hover:text-white transition-colors">
                  Pricing
                </a>
                <a href="#about" className="text-gray-300 hover:text-white transition-colors">
                  About
                </a>
              </nav>

              {/* CTA Buttons */}
              <div className="flex items-center space-x-4">
                <Link
                  to="/auth/login"
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                >
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="pt-24 pb-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* Hero Section */}
            <div className="text-center py-20">
              <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
                Welcome to <span className="text-purple-400">Unicorn Commander</span>
              </h1>
              <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
                Your all-in-one platform for AI-powered productivity and innovation
              </p>
              <Link
                to="/auth/login"
                className="inline-block px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-lg"
              >
                Get Started
              </Link>
            </div>

            {/* Features Section */}
            <div id="features" className="py-20">
              <h2 className="text-3xl font-bold text-white text-center mb-12">
                Powerful Features
              </h2>
              <div className="grid md:grid-cols-3 gap-8">
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-purple-500/20">
                  <h3 className="text-xl font-semibold text-white mb-3">AI Chat Interface</h3>
                  <p className="text-gray-300">
                    Advanced AI models at your fingertips with Open-WebUI integration
                  </p>
                </div>
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-purple-500/20">
                  <h3 className="text-xl font-semibold text-white mb-3">Smart Search</h3>
                  <p className="text-gray-300">
                    Center-Deep metasearch engine with 70+ search engines
                  </p>
                </div>
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-purple-500/20">
                  <h3 className="text-xl font-semibold text-white mb-3">Full Control</h3>
                  <p className="text-gray-300">
                    Comprehensive operations dashboard for complete system management
                  </p>
                </div>
              </div>
            </div>

            {/* Pricing Section */}
            <div id="pricing" className="py-20">
              <h2 className="text-3xl font-bold text-white text-center mb-12">
                Simple Pricing
              </h2>
              <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-8 border border-purple-500/20">
                  <h3 className="text-2xl font-semibold text-white mb-4">Starter</h3>
                  <p className="text-4xl font-bold text-purple-400 mb-6">$19<span className="text-lg text-gray-300">/mo</span></p>
                  <ul className="space-y-3 text-gray-300">
                    <li>✓ 1,000 API calls/month</li>
                    <li>✓ Basic AI models</li>
                    <li>✓ Email support</li>
                  </ul>
                </div>
                <div className="bg-purple-600/20 backdrop-blur-sm rounded-lg p-8 border-2 border-purple-400">
                  <div className="bg-purple-500 text-white text-sm font-semibold px-3 py-1 rounded-full inline-block mb-4">
                    Most Popular
                  </div>
                  <h3 className="text-2xl font-semibold text-white mb-4">Professional</h3>
                  <p className="text-4xl font-bold text-purple-400 mb-6">$49<span className="text-lg text-gray-300">/mo</span></p>
                  <ul className="space-y-3 text-gray-300">
                    <li>✓ 10,000 API calls/month</li>
                    <li>✓ All AI models</li>
                    <li>✓ Priority support</li>
                    <li>✓ Advanced features</li>
                  </ul>
                </div>
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-8 border border-purple-500/20">
                  <h3 className="text-2xl font-semibold text-white mb-4">Enterprise</h3>
                  <p className="text-4xl font-bold text-purple-400 mb-6">$99<span className="text-lg text-gray-300">/mo</span></p>
                  <ul className="space-y-3 text-gray-300">
                    <li>✓ Unlimited API calls</li>
                    <li>✓ Team management</li>
                    <li>✓ 24/7 dedicated support</li>
                    <li>✓ White-label options</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* About Section */}
            <div id="about" className="py-20 text-center">
              <h2 className="text-3xl font-bold text-white mb-6">
                About Unicorn Commander
              </h2>
              <p className="text-xl text-gray-300 max-w-3xl mx-auto mb-8">
                Magic Unicorn Unconventional Technology & Stuff Inc brings you cutting-edge AI infrastructure
                designed for the NVIDIA RTX 5090 GPU generation. Our platform combines powerful LLM inference,
                speech processing, document intelligence, and advanced search capabilities in one unified system.
              </p>
              <Link
                to="/auth/login"
                className="inline-block px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-lg"
              >
                Start Your Journey
              </Link>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="bg-slate-900/80 border-t border-purple-500/20 py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center text-gray-400">
              <p>&copy; 2025 Magic Unicorn Unconventional Technology & Stuff Inc. All rights reserved.</p>
              <p className="mt-2">
                <a href="https://your-domain.com" className="text-purple-400 hover:text-purple-300 transition-colors">
                  your-domain.com
                </a>
              </p>
            </div>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
}
