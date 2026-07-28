import React from 'react';
import { Box, Card, Typography } from '@mui/material';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid';

/**
 * StatsCard - Consistent analytics/stats card for admin pages
 *
 * Usage:
 *   <StatsCard
 *     title="Total Users"
 *     value="1,234"
 *     subtitle="Active accounts"
 *     trend={12.5}
 *     trendLabel="vs last month"
 *     color="primary"
 *     icon={UsersIcon}
 *   />
 *
 * Colors: 'primary' | 'success' | 'warning' | 'error' | 'info'
 */
export default function StatsCard({
  title,
  value,
  subtitle,
  trend,
  trendLabel = 'vs last period',
  color = 'primary',
  icon: Icon,
  onClick,
}) {
  const colorMap = {
    primary: {
      bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      light: 'rgba(102, 126, 234, 0.1)',
      text: '#667eea',
    },
    success: {
      bg: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
      light: 'rgba(17, 153, 142, 0.1)',
      text: '#11998e',
    },
    warning: {
      bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      light: 'rgba(245, 87, 108, 0.1)',
      text: '#f5576c',
    },
    error: {
      bg: 'linear-gradient(135deg, #eb3349 0%, #f45c43 100%)',
      light: 'rgba(235, 51, 73, 0.1)',
      text: '#eb3349',
    },
    info: {
      bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      light: 'rgba(79, 172, 254, 0.1)',
      text: '#4facfe',
    },
  };

  const colors = colorMap[color] || colorMap.primary;
  const isPositive = trend > 0;
  const isNegative = trend < 0;

  return (
    <Card
      onClick={onClick}
      sx={{
        p: 3,
        height: '100%',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease-in-out',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 3,
        '&:hover': onClick ? {
          transform: 'translateY(-2px)',
          boxShadow: 4,
        } : {},
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Box sx={{ flex: 1 }}>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontWeight: 500, mb: 1 }}
          >
            {title}
          </Typography>

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              mb: 0.5,
              background: colors.bg,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            {value}
          </Typography>

          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}

          {trend !== undefined && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
              {isPositive && (
                <ArrowUpIcon style={{ width: 16, height: 16, color: '#10b981' }} />
              )}
              {isNegative && (
                <ArrowDownIcon style={{ width: 16, height: 16, color: '#ef4444' }} />
              )}
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 600,
                  color: isPositive ? '#10b981' : isNegative ? '#ef4444' : 'text.secondary',
                }}
              >
                {isPositive ? '+' : ''}{trend}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {trendLabel}
              </Typography>
            </Box>
          )}
        </Box>

        {Icon && (
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              background: colors.light,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Icon style={{ width: 24, height: 24, color: colors.text }} />
          </Box>
        )}
      </Box>
    </Card>
  );
}
