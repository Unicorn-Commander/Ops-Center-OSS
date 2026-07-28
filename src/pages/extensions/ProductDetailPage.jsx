import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { getGlassmorphismStyles } from '../../styles/glassmorphism';
import AddToCartButton from '../../components/AddToCartButton';
import { useToast } from '../../components/Toast';

// Mock data - will be replaced with API call
const MOCK_ADDON = {
  id: 'tts',
  name: 'Text-to-Speech Service',
  tagline: 'Professional-grade voice synthesis with 20+ natural voices',
  price: 5.00,
  period: 'month',
  iconColor: 'from-pink-500 to-rose-500',
  description: `Transform text into natural-sounding speech with our advanced TTS service.
  Powered by state-of-the-art neural networks, our service delivers high-quality audio
  with emotion control, multiple voices, and support for various languages. Perfect for
  accessibility, content creation, and interactive applications.`,
  features: [
    {
      title: 'OpenAI-compatible API',
      description: 'Drop-in replacement for OpenAI TTS API with full compatibility'
    },
    {
      title: '20+ Natural Voices',
      description: 'Male and female voices in multiple languages and accents'
    },
    {
      title: 'Emotion & Speed Control',
      description: 'Adjust speaking rate and emotional tone for perfect delivery'
    },
    {
      title: 'SSML Support',
      description: 'Advanced control with Speech Synthesis Markup Language'
    },
    {
      title: 'Multiple Languages',
      description: 'Support for English, Spanish, French, German, and more'
    },
    {
      title: 'High-Quality Audio',
      description: '48kHz sample rate for crystal-clear output'
    }
  ],
  use_cases: [
    'Accessibility tools for visually impaired users',
    'Audiobook and podcast production',
    'E-learning and training content',
    'IVR and voice assistant systems',
    'Content creation and social media',
    'Game character voices and narration'
  ],
  screenshots: [], // Future feature
  related_addons: ['stt', 'brigade', 'analytics-advanced']
};

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

/**
 * Product Detail Page Component
 * Comprehensive add-on details with hero section, features, and related products
 */
export default function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { theme, currentTheme } = useTheme();
  const toast = useToast();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const [addon, setAddon] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load addon details
  useEffect(() => {
    // TODO: Replace with actual API call
    // extensionsApi.getAddon(id).then(data => setAddon(data.addon))

    // Mock implementation
    setTimeout(() => {
      setAddon(MOCK_ADDON);
      setLoading(false);
    }, 500);
  }, [id]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className={theme.text.secondary}>Loading add-on details...</p>
        </div>
      </div>
    );
  }

  if (!addon) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className={`${glassStyles.card} rounded-2xl p-12 text-center max-w-md`}>
          <h2 className={`text-2xl font-bold ${theme.text.primary} mb-4`}>
            Add-on Not Found
          </h2>
          <p className={`${theme.text.secondary} mb-6`}>
            The add-on you're looking for doesn't exist or has been removed.
          </p>
          <button
            onClick={() => navigate('/extensions')}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-lg font-semibold transition-all shadow-lg"
          >
            Back to Extensions
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-6xl mx-auto px-4 py-8 space-y-8"
    >
      {/* Back Button */}
      <motion.button
        variants={itemVariants}
        onClick={() => navigate('/extensions')}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg ${glassStyles.card} hover:bg-white/10 transition-colors`}
      >
        <ArrowLeftIcon className={`h-5 w-5 ${theme.text.secondary}`} />
        <span className={`text-sm ${theme.text.secondary}`}>Back to Extensions</span>
      </motion.button>

      {/* Hero Section */}
      <motion.div
        variants={itemVariants}
        className={`${glassStyles.card} rounded-3xl p-8 lg:p-12`}
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          {/* Left Column - Icon & Info */}
          <div className="space-y-6">
            {/* Icon */}
            <div className={`w-24 h-24 bg-gradient-to-br ${addon.iconColor} rounded-3xl flex items-center justify-center shadow-2xl`}>
              <SparklesIcon className="h-12 w-12 text-white" />
            </div>

            {/* Title & Tagline */}
            <div>
              <h1 className={`text-4xl font-bold ${theme.text.primary} mb-3`}>
                {addon.name}
              </h1>
              <p className={`text-lg ${theme.text.secondary}`}>
                {addon.tagline}
              </p>
            </div>

            {/* Pricing */}
            <div className="flex items-baseline gap-3">
              <span className={`text-5xl font-bold ${theme.text.primary}`}>
                {formatCurrency(addon.price)}
              </span>
              <span className={`text-xl ${theme.text.secondary}`}>
                / {addon.period}
              </span>
            </div>
          </div>

          {/* Right Column - CTA */}
          <div className="flex flex-col items-center gap-6">
            <AddToCartButton
              addon_id={addon.id}
              addon_name={addon.name}
              variant="primary"
              size="large"
              className="w-full py-4 text-xl"
              onSuccess={() => navigate('/extensions/checkout')}
            />

            <div className={`${glassStyles.card} rounded-xl p-4 w-full`}>
              <h3 className={`text-sm font-bold ${theme.text.primary} mb-3`}>
                What's included:
              </h3>
              <ul className={`space-y-2 text-sm ${theme.text.secondary}`}>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Instant activation</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Cancel anytime</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>24/7 support</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Description Section */}
      <motion.div
        variants={itemVariants}
        className={`${glassStyles.card} rounded-2xl p-8`}
      >
        <h2 className={`text-2xl font-bold ${theme.text.primary} mb-4`}>
          Description
        </h2>
        <p className={`text-base ${theme.text.secondary} leading-relaxed whitespace-pre-line`}>
          {addon.description}
        </p>
      </motion.div>

      {/* Features Grid */}
      <motion.div
        variants={itemVariants}
        className={`${glassStyles.card} rounded-2xl p-8`}
      >
        <h2 className={`text-2xl font-bold ${theme.text.primary} mb-6`}>
          Key Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {addon.features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`${glassStyles.card} rounded-xl p-5`}
            >
              <div className="flex items-start gap-3">
                <CheckCircleIcon className="h-6 w-6 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className={`text-lg font-semibold ${theme.text.primary} mb-1`}>
                    {feature.title}
                  </h3>
                  <p className={`text-sm ${theme.text.secondary}`}>
                    {feature.description}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Use Cases */}
      <motion.div
        variants={itemVariants}
        className={`${glassStyles.card} rounded-2xl p-8`}
      >
        <h2 className={`text-2xl font-bold ${theme.text.primary} mb-6`}>
          Use Cases
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {addon.use_cases.map((useCase, index) => (
            <div
              key={index}
              className={`${glassStyles.card} rounded-lg p-4 flex items-start gap-2`}
            >
              <SparklesIcon className={`h-5 w-5 ${theme.text.accent} flex-shrink-0 mt-0.5`} />
              <span className={`text-sm ${theme.text.secondary}`}>
                {useCase}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Bottom CTA */}
      <motion.div
        variants={itemVariants}
        className={`${glassStyles.card} rounded-2xl p-8 text-center`}
      >
        <h2 className={`text-2xl font-bold ${theme.text.primary} mb-4`}>
          Ready to get started?
        </h2>
        <p className={`${theme.text.secondary} mb-6`}>
          Add {addon.name} to your subscription today
        </p>
        <AddToCartButton
          addon_id={addon.id}
          addon_name={addon.name}
          variant="primary"
          size="large"
          className="inline-flex"
          onSuccess={() => navigate('/extensions/checkout')}
        />
      </motion.div>
    </motion.div>
  );
}
