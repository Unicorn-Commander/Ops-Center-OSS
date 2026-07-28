/**
 * DashboardSkeleton Component
 *
 * Loading skeleton that matches DashboardPro layout
 * Shows during data loading to prevent layout shift
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { useResponsive } from '../hooks/useResponsive';

const SkeletonBox = ({ className, animate = true }) => (
  <div
    className={`
      ${className}
      ${animate ? 'animate-pulse' : ''}
      bg-gradient-to-r from-gray-800/30 to-gray-700/30
      rounded-xl
    `}
  />
);

const SkeletonCircle = ({ size = 'md', animate = true }) => {
  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-20 h-20',
    lg: 'w-32 h-32',
  };

  return (
    <div
      className={`
        ${sizeClasses[size]}
        ${animate ? 'animate-pulse' : ''}
        bg-gradient-to-br from-gray-800/30 to-gray-700/30
        rounded-full
      `}
    />
  );
};

const MetricCardSkeleton = ({ theme }) => (
  <div
    className={`
      p-6 rounded-2xl
      bg-gradient-to-br from-gray-800/40 to-gray-900/40
      border border-gray-700/50 backdrop-blur-xl
    `}
  >
    <div className="flex items-start justify-between mb-4">
      <SkeletonBox className="w-12 h-12 rounded-xl" />
      <SkeletonBox className="w-16 h-6" />
    </div>

    <div className="space-y-2">
      <SkeletonBox className="w-24 h-4" />
      <SkeletonBox className="w-32 h-8" />
      <SkeletonBox className="w-40 h-3" />
    </div>
  </div>
);

const ResourceGaugeSkeleton = () => (
  <div className="space-y-3">
    <div className="flex items-center justify-between">
      <SkeletonBox className="w-32 h-4" />
      <SkeletonBox className="w-12 h-4" />
    </div>

    <SkeletonBox className="w-full h-2 rounded-full" />

    <div className="flex justify-between">
      <SkeletonBox className="w-24 h-3" />
      <SkeletonBox className="w-24 h-3" />
    </div>
  </div>
);

const ServiceCardSkeleton = () => (
  <div
    className={`
      relative p-4 rounded-xl
      bg-gradient-to-br from-gray-800/50 to-gray-900/50
      border border-gray-700/50 backdrop-blur-sm
    `}
  >
    <div className="flex flex-col items-center gap-2">
      <SkeletonCircle size="sm" />
      <SkeletonBox className="w-20 h-4" />
      <SkeletonCircle size="sm" />
    </div>
  </div>
);

const DashboardSkeleton = () => {
  const { theme } = useTheme();
  const { isMobile, isTablet, getGridColumns } = useResponsive();

  const gridCols = getGridColumns();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-6 p-6"
    >
      {/* Header Skeleton */}
      <div className="relative">
        <div className="flex items-center justify-between">
          <div className="space-y-3">
            <SkeletonBox className="w-64 h-10" />
            <SkeletonBox className="w-96 h-5" />
          </div>

          {!isMobile && (
            <div className="text-right space-y-2">
              <SkeletonBox className="w-32 h-4 ml-auto" />
              <div className="flex items-center gap-3 justify-end">
                <SkeletonBox className="w-20 h-10" />
                <SkeletonCircle size="lg" />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Key Metrics Grid Skeleton */}
      <div
        className={`
          grid gap-4
          ${isMobile ? 'grid-cols-1' : isTablet ? 'grid-cols-2' : 'grid-cols-4'}
        `}
      >
        <MetricCardSkeleton theme={theme} />
        <MetricCardSkeleton theme={theme} />
        <MetricCardSkeleton theme={theme} />
        <MetricCardSkeleton theme={theme} />
      </div>

      {/* Quick Actions Bar Skeleton */}
      <div
        className={`
          p-4 rounded-2xl
          bg-gradient-to-r from-purple-900/20 via-indigo-900/20 to-blue-900/20
          border border-purple-500/20 backdrop-blur-xl
        `}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <SkeletonCircle size="sm" />
            <SkeletonBox className="w-32 h-5" />
          </div>

          {!isMobile && (
            <div className="flex items-center gap-2">
              <SkeletonBox className="w-32 h-10 rounded-lg" />
              <SkeletonBox className="w-24 h-10 rounded-lg" />
              <SkeletonBox className="w-32 h-10 rounded-lg" />
            </div>
          )}
        </div>
      </div>

      {/* Main Content Grid Skeleton */}
      <div className={`grid gap-6 ${isMobile ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-3'}`}>
        {/* Resource Monitoring Skeleton */}
        <div
          className={`
            ${isMobile ? 'col-span-1' : 'lg:col-span-2'}
            p-6 rounded-2xl
            bg-gradient-to-br from-gray-800/40 to-gray-900/40
            border border-gray-700/50 backdrop-blur-xl
          `}
        >
          <div className="flex items-center justify-between mb-6">
            <SkeletonBox className="w-48 h-6" />
            <SkeletonBox className="w-24 h-5" />
          </div>

          <div className="space-y-6">
            <ResourceGaugeSkeleton />
            <ResourceGaugeSkeleton />
            <ResourceGaugeSkeleton />
            <ResourceGaugeSkeleton />
          </div>
        </div>

        {/* System Information Skeleton */}
        <div
          className={`
            p-6 rounded-2xl
            bg-gradient-to-br from-gray-800/40 to-gray-900/40
            border border-gray-700/50 backdrop-blur-xl
          `}
        >
          <SkeletonBox className="w-48 h-6 mb-6" />

          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="p-4 rounded-xl bg-gray-800/50 backdrop-blur-sm">
                <SkeletonBox className="w-24 h-3 mb-2" />
                <SkeletonBox className="w-full h-5 mb-1" />
                <SkeletonBox className="w-40 h-3" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Services Status Skeleton */}
      <div
        className={`
          p-6 rounded-2xl
          bg-gradient-to-br from-gray-800/40 to-gray-900/40
          border border-gray-700/50 backdrop-blur-xl
        `}
      >
        <div className="flex items-center justify-between mb-6">
          <SkeletonBox className="w-40 h-6" />
          <div className="flex items-center gap-4">
            <SkeletonBox className="w-24 h-5" />
            <SkeletonBox className="w-24 h-5" />
          </div>
        </div>

        <div
          className={`
            grid gap-3
            ${
              isMobile
                ? 'grid-cols-2'
                : isTablet
                ? 'grid-cols-3'
                : 'grid-cols-6'
            }
          `}
        >
          {Array.from({ length: isMobile ? 4 : isTablet ? 6 : 12 }).map((_, i) => (
            <ServiceCardSkeleton key={i} />
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default DashboardSkeleton;
