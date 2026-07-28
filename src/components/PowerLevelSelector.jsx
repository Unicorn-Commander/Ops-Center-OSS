/**
 * PowerLevelSelector Component
 *
 * Three-way toggle for selecting LLM power levels with cost/speed/quality indicators
 *
 * Power Levels:
 * - Eco: Fast, cheap models (GPT-3.5, Claude Haiku) - ~$0.50/1M tokens
 * - Balanced: Mid-tier models (GPT-4, Claude Sonnet) - ~$5/1M tokens
 * - Precision: Best models (GPT-4 Turbo, Claude Opus) - ~$100/1M tokens
 *
 * Props:
 * - value: 'eco' | 'balanced' | 'precision' - Current selected level
 * - onChange: (level: string) => void - Callback when level changes
 * - compact: boolean - Compact mode for inline use (default: false)
 * - showEstimates: boolean - Show cost/speed estimates (default: true)
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BoltIcon,
  CurrencyDollarIcon,
  StarIcon,
  ServerIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function PowerLevelSelector({
  value,
  onChange,
  compact = false,
  showEstimates = true
}) {
  const { theme, currentTheme } = useTheme();
  const [estimates, setEstimates] = useState(null);
  const [loading, setLoading] = useState(false);

  const powerLevels = [
    {
      id: 'eco',
      name: 'Eco',
      icon: '💸',
      color: 'green',
      description: 'Fast & affordable',
      costRange: '$0.50/1M tokens',
      speedRange: '~500ms',
      quality: 'Good'
    },
    {
      id: 'balanced',
      name: 'Balanced',
      icon: '⚖️',
      color: 'blue',
      description: 'Best value for quality',
      costRange: '$5/1M tokens',
      speedRange: '~1000ms',
      quality: 'Great'
    },
    {
      id: 'precision',
      name: 'Precision',
      icon: '🎯',
      color: 'purple',
      description: 'Highest quality & accuracy',
      costRange: '$100/1M tokens',
      speedRange: '~2000ms',
      quality: 'Best'
    }
  ];

  const getThemeClasses = () => ({
    card: currentTheme === 'unicorn'
      ? 'bg-purple-900/50 backdrop-blur-xl border-white/20'
      : currentTheme === 'light'
      ? 'bg-white border-gray-200'
      : 'bg-slate-800 border-slate-700',
    text: currentTheme === 'unicorn'
      ? 'text-purple-100'
      : currentTheme === 'light'
      ? 'text-gray-900'
      : 'text-slate-100',
    subtext: currentTheme === 'unicorn'
      ? 'text-purple-300'
      : currentTheme === 'light'
      ? 'text-gray-600'
      : 'text-slate-400'
  });

  const themeClasses = getThemeClasses();

  useEffect(() => {
    if (!compact && showEstimates) {
      loadEstimates();
    }
  }, [value, compact, showEstimates]);

  const loadEstimates = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/llm/power-levels/${value}/estimate`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setEstimates(data);
      } else {
        // Use fallback data if API fails
        setEstimates(null);
      }
    } catch (error) {
      console.error('Failed to load estimates:', error);
      setEstimates(null);
    } finally {
      setLoading(false);
    }
  };

  const getButtonClasses = (level) => {
    const isActive = value === level.id;
    const baseClasses = 'px-4 py-2 rounded-lg font-medium transition-all';

    if (isActive) {
      switch (level.color) {
        case 'green':
          return `${baseClasses} bg-green-500 text-white shadow-lg shadow-green-500/50`;
        case 'blue':
          return `${baseClasses} bg-blue-500 text-white shadow-lg shadow-blue-500/50`;
        case 'purple':
          return `${baseClasses} bg-purple-500 text-white shadow-lg shadow-purple-500/50`;
        default:
          return `${baseClasses} bg-gray-500 text-white`;
      }
    }

    return `${baseClasses} ${
      currentTheme === 'light'
        ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
    }`;
  };

  // Compact mode for inline use
  if (compact) {
    return (
      <div className="flex gap-2">
        {powerLevels.map(level => (
          <button
            key={level.id}
            onClick={() => onChange(level.id)}
            className={getButtonClasses(level)}
            title={`${level.name}: ${level.description}`}
          >
            <span className="mr-1">{level.icon}</span>
            {level.name}
          </button>
        ))}
      </div>
    );
  }

  // Full mode with estimates
  return (
    <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
      <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
        Power Level
      </h3>

      {/* Toggle Buttons */}
      <div className="flex gap-3 mb-6">
        {powerLevels.map(level => (
          <motion.button
            key={level.id}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onChange(level.id)}
            className={`flex-1 ${getButtonClasses(level)}`}
          >
            <div className="text-center">
              <div className="text-2xl mb-1">{level.icon}</div>
              <div className="font-semibold">{level.name}</div>
              <div className="text-xs opacity-75 mt-1">{level.description}</div>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Estimates */}
      {showEstimates && (
        <div className="space-y-3">
          {loading ? (
            <div className="flex items-center justify-center py-6">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
            </div>
          ) : estimates ? (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CurrencyDollarIcon className="h-5 w-5 text-green-400" />
                  <span className={themeClasses.subtext}>Est. Cost:</span>
                </div>
                <span className={themeClasses.text}>
                  ${estimates.cost_per_request?.toFixed(4) || '0.0000'}/request
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BoltIcon className="h-5 w-5 text-yellow-400" />
                  <span className={themeClasses.subtext}>Est. Speed:</span>
                </div>
                <span className={themeClasses.text}>
                  ~{estimates.avg_latency || '1000'}ms
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <StarIcon className="h-5 w-5 text-purple-400" />
                  <span className={themeClasses.subtext}>Quality:</span>
                </div>
                <span className={themeClasses.text}>
                  {estimates.quality_level || powerLevels.find(l => l.id === value)?.quality}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ServerIcon className="h-5 w-5 text-blue-400" />
                  <span className={themeClasses.subtext}>Default Model:</span>
                </div>
                <span className={`text-sm ${themeClasses.text}`}>
                  {estimates.default_model || 'GPT-3.5 Turbo'}
                </span>
              </div>
            </>
          ) : (
            // Fallback to static data
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CurrencyDollarIcon className="h-5 w-5 text-green-400" />
                  <span className={themeClasses.subtext}>Cost Range:</span>
                </div>
                <span className={themeClasses.text}>
                  {powerLevels.find(l => l.id === value)?.costRange}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BoltIcon className="h-5 w-5 text-yellow-400" />
                  <span className={themeClasses.subtext}>Speed:</span>
                </div>
                <span className={themeClasses.text}>
                  {powerLevels.find(l => l.id === value)?.speedRange}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <StarIcon className="h-5 w-5 text-purple-400" />
                  <span className={themeClasses.subtext}>Quality:</span>
                </div>
                <span className={themeClasses.text}>
                  {powerLevels.find(l => l.id === value)?.quality}
                </span>
              </div>
            </>
          )}
        </div>
      )}

      {/* Info Box */}
      <div className={`mt-4 p-3 rounded-lg ${
        currentTheme === 'light'
          ? 'bg-blue-50 border border-blue-200'
          : 'bg-blue-500/10 border border-blue-500/30'
      }`}>
        <p className={`text-xs ${themeClasses.text}`}>
          <strong>{powerLevels.find(l => l.id === value)?.name}:</strong>{' '}
          {powerLevels.find(l => l.id === value)?.description}.
          Automatically routes to the best available model in this tier.
        </p>
      </div>
    </div>
  );
}
