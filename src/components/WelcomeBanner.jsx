import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Chip } from '@mui/material';
import { motion } from 'framer-motion';
import {
  SparklesIcon,
  ClockIcon,
  ServerIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function WelcomeBanner({ user, stats }) {
  const { theme, currentTheme } = useTheme();
  const [greeting, setGreeting] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Determine greeting based on time of day
  useEffect(() => {
    const hour = currentTime.getHours();
    if (hour < 12) {
      setGreeting('Good morning');
    } else if (hour < 18) {
      setGreeting('Good afternoon');
    } else {
      setGreeting('Good evening');
    }
  }, [currentTime]);

  // Format time
  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  };

  // Format date
  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Get tier badge color
  const getTierColor = (tier) => {
    const tierColors = {
      trial: { bg: 'bg-gray-600', text: 'text-gray-100' },
      starter: { bg: 'bg-blue-600', text: 'text-blue-100' },
      professional: { bg: 'bg-purple-600', text: 'text-purple-100' },
      enterprise: { bg: 'bg-yellow-600', text: 'text-yellow-100' }
    };
    return tierColors[tier?.toLowerCase()] || tierColors.trial;
  };

  const tierColor = getTierColor(user?.subscription_tier);

  // Glassmorphism gradient based on theme
  const getGradient = () => {
    if (currentTheme === 'unicorn') {
      return 'from-purple-900/40 via-violet-900/30 to-indigo-900/40';
    } else if (currentTheme === 'light') {
      return 'from-blue-50/80 via-indigo-50/60 to-purple-50/80';
    } else {
      return 'from-slate-800/40 via-blue-900/30 to-slate-800/40';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
    >
      <Card
        className={`${theme.card} overflow-hidden relative`}
        sx={{
          background: currentTheme === 'light'
            ? 'linear-gradient(135deg, rgba(249, 250, 251, 0.9), rgba(238, 242, 255, 0.8), rgba(243, 232, 255, 0.8))'
            : currentTheme === 'unicorn'
            ? 'linear-gradient(135deg, rgba(88, 28, 135, 0.4), rgba(91, 33, 182, 0.3), rgba(67, 56, 202, 0.4))'
            : 'linear-gradient(135deg, rgba(30, 41, 59, 0.4), rgba(30, 58, 138, 0.3), rgba(30, 41, 59, 0.4))',
          backdropFilter: 'blur(10px)',
          border: currentTheme === 'unicorn'
            ? '1px solid rgba(168, 85, 247, 0.2)'
            : currentTheme === 'light'
            ? '1px solid rgba(219, 234, 254, 0.5)'
            : '1px solid rgba(148, 163, 184, 0.1)'
        }}
      >
        {/* Animated background effect */}
        <Box
          className="absolute inset-0 opacity-30"
          sx={{
            background: currentTheme === 'unicorn'
              ? 'radial-gradient(circle at 20% 50%, rgba(168, 85, 247, 0.15), transparent 50%), radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.15), transparent 50%)'
              : currentTheme === 'light'
              ? 'radial-gradient(circle at 20% 50%, rgba(147, 197, 253, 0.2), transparent 50%), radial-gradient(circle at 80% 80%, rgba(196, 181, 253, 0.2), transparent 50%)'
              : 'radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.15), transparent 50%), radial-gradient(circle at 80% 80%, rgba(99, 102, 241, 0.15), transparent 50%)'
          }}
        />

        <CardContent className="p-6 relative z-10">
          <Box className="flex items-center justify-between">
            {/* Left side: Greeting and stats */}
            <Box className="flex-1">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Box className="flex items-center gap-2 mb-2">
                  <SparklesIcon
                    className={`h-8 w-8 ${
                      currentTheme === 'unicorn'
                        ? 'text-yellow-400'
                        : currentTheme === 'light'
                        ? 'text-blue-600'
                        : 'text-blue-400'
                    }`}
                  />
                  <Typography
                    variant="h4"
                    className={`font-bold ${
                      currentTheme === 'light' ? 'text-gray-900' : theme.text.primary
                    }`}
                  >
                    {greeting}, {user?.username || user?.name || 'Admin'}!
                  </Typography>
                </Box>

                <Typography
                  variant="body1"
                  className={`${
                    currentTheme === 'light' ? 'text-gray-600' : theme.text.secondary
                  } mb-3`}
                >
                  {formatDate(currentTime)}
                </Typography>

                {/* Quick stats */}
                <Box className="flex items-center gap-4 mt-4">
                  <Box className="flex items-center gap-2">
                    <ServerIcon
                      className={`h-5 w-5 ${
                        currentTheme === 'unicorn'
                          ? 'text-violet-400'
                          : currentTheme === 'light'
                          ? 'text-blue-600'
                          : 'text-blue-400'
                      }`}
                    />
                    <Typography
                      variant="body2"
                      className={currentTheme === 'light' ? 'text-gray-700' : theme.text.primary}
                    >
                      <span className="font-semibold">{stats?.activeServices || 0}</span> active services
                    </Typography>
                  </Box>

                  <Box className="flex items-center gap-2">
                    <ClockIcon
                      className={`h-5 w-5 ${
                        currentTheme === 'unicorn'
                          ? 'text-violet-400'
                          : currentTheme === 'light'
                          ? 'text-blue-600'
                          : 'text-blue-400'
                      }`}
                    />
                    <Typography
                      variant="body2"
                      className={`font-mono ${
                        currentTheme === 'light' ? 'text-gray-700' : theme.text.primary
                      }`}
                    >
                      {formatTime(currentTime)}
                    </Typography>
                  </Box>
                </Box>
              </motion.div>
            </Box>

            {/* Right side: Tier badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4, type: "spring", stiffness: 200 }}
            >
              <Box className="text-right">
                <Typography
                  variant="caption"
                  className={`${
                    currentTheme === 'light' ? 'text-gray-600' : theme.text.secondary
                  } block mb-2`}
                >
                  Subscription Tier
                </Typography>
                <Chip
                  label={(user?.subscription_tier || 'Trial').toUpperCase()}
                  className={`${tierColor.bg} ${tierColor.text} font-bold px-4 py-5 text-sm shadow-lg`}
                  sx={{
                    borderRadius: '12px',
                    fontSize: '0.875rem',
                    fontWeight: 700,
                    letterSpacing: '0.05em'
                  }}
                />
              </Box>
            </motion.div>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
}
