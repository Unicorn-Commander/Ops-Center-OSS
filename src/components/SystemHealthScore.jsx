import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, LinearProgress, Collapse, IconButton } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ChevronDownIcon,
  CpuChipIcon,
  ServerIcon,
  CircleStackIcon,
  SignalIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function SystemHealthScore({ score, details, isLoading = false }) {
  const { theme, currentTheme } = useTheme();
  const [expanded, setExpanded] = useState(false);
  const [displayScore, setDisplayScore] = useState(0);

  // Animate score counter on mount
  useEffect(() => {
    if (!isLoading && score !== undefined) {
      const duration = 2000; // 2 seconds
      const steps = 60;
      const increment = score / steps;
      let current = 0;
      let step = 0;

      const timer = setInterval(() => {
        step++;
        current = Math.min(Math.floor(increment * step), score);
        setDisplayScore(current);

        if (step >= steps) {
          clearInterval(timer);
        }
      }, duration / steps);

      return () => clearInterval(timer);
    }
  }, [score, isLoading]);

  // Determine health status
  const getHealthStatus = (score) => {
    if (score >= 80) return { level: 'healthy', label: 'Healthy', color: 'emerald' };
    if (score >= 50) return { level: 'degraded', label: 'Degraded', color: 'yellow' };
    return { level: 'critical', label: 'Critical', color: 'red' };
  };

  const healthStatus = getHealthStatus(score || 0);

  // Color configurations
  const colorMap = {
    emerald: {
      gradient: 'from-emerald-500 to-green-500',
      text: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      icon: CheckCircleIcon
    },
    yellow: {
      gradient: 'from-yellow-500 to-amber-500',
      text: 'text-yellow-400',
      bg: 'bg-yellow-500/10',
      border: 'border-yellow-500/30',
      icon: ExclamationTriangleIcon
    },
    red: {
      gradient: 'from-red-500 to-rose-500',
      text: 'text-red-400',
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      icon: XCircleIcon
    }
  };

  const colors = colorMap[healthStatus.color];
  const StatusIcon = colors.icon;

  // Subsystem metrics
  const subsystems = details || [
    { name: 'CPU', value: 75, icon: CpuChipIcon, status: 'healthy' },
    { name: 'Memory', value: 68, icon: ServerIcon, status: 'healthy' },
    { name: 'Disk', value: 45, icon: CircleStackIcon, status: 'degraded' },
    { name: 'Network', value: 92, icon: SignalIcon, status: 'healthy' }
  ];

  const getSubsystemColor = (value) => {
    if (value >= 80) return 'text-emerald-400';
    if (value >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Card
        className={`${theme.card} overflow-hidden cursor-pointer hover:shadow-2xl transition-all duration-300`}
        onClick={() => setExpanded(!expanded)}
      >
        <CardContent className="p-6">
          {/* Main Health Display */}
          <Box className="flex items-center justify-between mb-4">
            <Box>
              <Typography variant="subtitle2" className={`${theme.text.secondary} mb-1`}>
                System Health
              </Typography>
              <Box className="flex items-center gap-2">
                <Typography
                  variant="h3"
                  className={`font-bold ${colors.text}`}
                >
                  {isLoading ? '...' : `${displayScore}%`}
                </Typography>
                <Box className={`px-3 py-1 rounded-full ${colors.bg} border ${colors.border}`}>
                  <Typography variant="caption" className={`font-semibold ${colors.text}`}>
                    {healthStatus.label}
                  </Typography>
                </Box>
              </Box>
            </Box>

            {/* Circular Progress Indicator */}
            <Box className="relative">
              <svg className="transform -rotate-90 w-32 h-32">
                {/* Background circle */}
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  className="text-gray-700"
                />
                {/* Progress circle */}
                <motion.circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 56}`}
                  initial={{ strokeDashoffset: 2 * Math.PI * 56 }}
                  animate={{ strokeDashoffset: 2 * Math.PI * 56 * (1 - (displayScore / 100)) }}
                  transition={{ duration: 2, ease: "easeOut" }}
                  className={`${colors.text} drop-shadow-lg`}
                />
              </svg>
              {/* Center Icon */}
              <Box className="absolute inset-0 flex items-center justify-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.5, type: "spring", stiffness: 200 }}
                >
                  <StatusIcon className={`h-12 w-12 ${colors.text}`} />
                </motion.div>
              </Box>
            </Box>
          </Box>

          {/* Expand/Collapse Indicator */}
          <Box className="flex items-center justify-center">
            <motion.div
              animate={{ rotate: expanded ? 180 : 0 }}
              transition={{ duration: 0.3 }}
            >
              <ChevronDownIcon className={`h-5 w-5 ${theme.text.secondary}`} />
            </motion.div>
          </Box>

          {/* Expandable Subsystem Details */}
          <Collapse in={expanded}>
            <Box className="mt-6 pt-6 border-t border-gray-700">
              <Typography variant="subtitle2" className={`${theme.text.secondary} mb-4`}>
                Subsystem Status
              </Typography>

              <Box className="space-y-4">
                {subsystems.map((subsystem, index) => {
                  const SubIcon = subsystem.icon;
                  return (
                    <motion.div
                      key={subsystem.name}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <Box className="flex items-center justify-between mb-2">
                        <Box className="flex items-center gap-2">
                          <SubIcon className={`h-4 w-4 ${theme.text.secondary}`} />
                          <Typography variant="body2" className={theme.text.primary}>
                            {subsystem.name}
                          </Typography>
                        </Box>
                        <Typography
                          variant="body2"
                          className={`font-semibold ${getSubsystemColor(subsystem.value)}`}
                        >
                          {subsystem.value}%
                        </Typography>
                      </Box>

                      {/* Progress bar */}
                      <Box className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
                        <motion.div
                          className={`absolute inset-y-0 left-0 bg-gradient-to-r ${
                            subsystem.value >= 80
                              ? 'from-emerald-500 to-green-500'
                              : subsystem.value >= 50
                              ? 'from-yellow-500 to-amber-500'
                              : 'from-red-500 to-rose-500'
                          } rounded-full`}
                          initial={{ width: 0 }}
                          animate={{ width: `${subsystem.value}%` }}
                          transition={{ duration: 1, delay: index * 0.1 }}
                        />
                      </Box>
                    </motion.div>
                  );
                })}
              </Box>
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    </motion.div>
  );
}
