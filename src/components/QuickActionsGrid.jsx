import React from 'react';
import { Box, Card, CardContent, Typography, Grid } from '@mui/material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  UserPlusIcon,
  CreditCardIcon,
  DocumentMagnifyingGlassIcon,
  ServerIcon,
  Cog6ToothIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function QuickActionsGrid() {
  const { theme, currentTheme } = useTheme();
  const navigate = useNavigate();

  const actions = [
    {
      title: 'Add User',
      description: 'Create new user account',
      icon: UserPlusIcon,
      color: 'blue',
      path: '/admin/people/users',
      action: 'create',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      title: 'View Billing',
      description: 'Manage subscriptions & invoices',
      icon: CreditCardIcon,
      color: 'green',
      path: '/admin/billing/system',
      gradient: 'from-emerald-500 to-green-500'
    },
    {
      title: 'Check Logs',
      description: 'System activity & errors',
      icon: DocumentMagnifyingGlassIcon,
      color: 'purple',
      path: '/admin/monitoring/logs',
      gradient: 'from-purple-500 to-indigo-500'
    },
    {
      title: 'Manage Services',
      description: 'Start, stop, restart services',
      icon: ServerIcon,
      color: 'orange',
      path: '/admin/infra/services',
      gradient: 'from-orange-500 to-amber-500'
    },
    {
      title: 'System Settings',
      description: 'Configure system parameters',
      icon: Cog6ToothIcon,
      color: 'slate',
      path: '/admin/system/settings',
      gradient: 'from-slate-500 to-gray-500'
    },
    {
      title: 'View Analytics',
      description: 'Usage metrics & trends',
      icon: ChartBarIcon,
      color: 'pink',
      path: '/admin/monitoring/analytics',
      gradient: 'from-pink-500 to-rose-500'
    }
  ];

  const handleActionClick = (action) => {
    if (action.path) {
      navigate(action.path);
    }
  };

  return (
    <Grid container spacing={3}>
      {actions.map((action, index) => {
        const Icon = action.icon;

        return (
          <Grid item xs={12} sm={6} md={4} key={action.title}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              whileHover={{ scale: 1.05, y: -5 }}
              whileTap={{ scale: 0.98 }}
            >
              <Card
                onClick={() => handleActionClick(action)}
                className={`${theme.card} overflow-hidden cursor-pointer hover:shadow-2xl transition-all duration-300 h-full`}
                sx={{
                  background: currentTheme === 'light'
                    ? 'linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(249, 250, 251, 0.8))'
                    : currentTheme === 'unicorn'
                    ? 'linear-gradient(135deg, rgba(30, 27, 75, 0.6), rgba(88, 28, 135, 0.4))'
                    : 'linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(51, 65, 85, 0.4))',
                  backdropFilter: 'blur(10px)',
                  border: currentTheme === 'unicorn'
                    ? '1px solid rgba(168, 85, 247, 0.2)'
                    : currentTheme === 'light'
                    ? '1px solid rgba(229, 231, 235, 0.5)'
                    : '1px solid rgba(148, 163, 184, 0.1)',
                  '&:hover': {
                    boxShadow: currentTheme === 'unicorn'
                      ? '0 20px 40px rgba(168, 85, 247, 0.3)'
                      : currentTheme === 'light'
                      ? '0 20px 40px rgba(59, 130, 246, 0.2)'
                      : '0 20px 40px rgba(59, 130, 246, 0.15)'
                  }
                }}
              >
                {/* Hover glow effect */}
                <Box
                  className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-500"
                  sx={{
                    background: `linear-gradient(135deg, transparent, rgba(168, 85, 247, 0.1))`
                  }}
                />

                <CardContent className="p-6 relative z-10">
                  {/* Icon container */}
                  <Box className="mb-4">
                    <Box
                      className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${action.gradient} shadow-lg`}
                      sx={{
                        boxShadow: currentTheme === 'unicorn'
                          ? `0 8px 24px rgba(168, 85, 247, 0.3)`
                          : `0 8px 24px rgba(59, 130, 246, 0.2)`
                      }}
                    >
                      <Icon className="h-8 w-8 text-white" />
                    </Box>
                  </Box>

                  {/* Title */}
                  <Typography
                    variant="h6"
                    className={`font-bold mb-2 ${
                      currentTheme === 'light' ? 'text-gray-900' : theme.text.primary
                    }`}
                  >
                    {action.title}
                  </Typography>

                  {/* Description */}
                  <Typography
                    variant="body2"
                    className={currentTheme === 'light' ? 'text-gray-600' : theme.text.secondary}
                  >
                    {action.description}
                  </Typography>

                  {/* Pulse animation for important actions */}
                  {(action.title === 'Check Logs' || action.title === 'Manage Services') && (
                    <motion.div
                      className="absolute top-4 right-4"
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.5, 1, 0.5]
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    >
                      <Box
                        className={`w-2 h-2 rounded-full ${
                          action.title === 'Check Logs' ? 'bg-yellow-400' : 'bg-blue-400'
                        }`}
                      />
                    </motion.div>
                  )}
                </CardContent>

                {/* Bottom accent line */}
                <Box
                  className="h-1"
                  sx={{
                    background: `linear-gradient(to right, ${
                      currentTheme === 'unicorn'
                        ? 'rgba(168, 85, 247, 0.5)'
                        : currentTheme === 'light'
                        ? 'rgba(59, 130, 246, 0.5)'
                        : 'rgba(59, 130, 246, 0.3)'
                    }, transparent)`
                  }}
                />
              </Card>
            </motion.div>
          </Grid>
        );
      })}
    </Grid>
  );
}
