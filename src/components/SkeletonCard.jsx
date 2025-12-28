import React from 'react';
import { motion } from 'framer-motion';

export default function SkeletonCard({ className = "", rows = 3 }) {
  return (
    <motion.div 
      className={`bg-gray-800/50 backdrop-blur-md border border-gray-700/30 rounded-lg p-4 ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="animate-pulse">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="h-6 bg-gray-700 rounded w-32"></div>
          <div className="h-4 bg-gray-700 rounded w-16"></div>
        </div>
        
        {/* Content rows */}
        {Array.from({ length: rows }).map((_, index) => (
          <div key={index} className="mb-3 last:mb-0">
            <div className="flex items-center justify-between">
              <div className={`h-4 bg-gray-700 rounded ${
                index === 0 ? 'w-3/4' : 
                index === 1 ? 'w-1/2' : 'w-2/3'
              }`}></div>
              <div className="h-4 bg-gray-700 rounded w-16"></div>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export function SkeletonList({ items = 5, className = "" }) {
  return (
    <div className={`space-y-4 ${className}`}>
      {Array.from({ length: items }).map((_, index) => (
        <SkeletonCard key={index} rows={2} />
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4, className = "" }) {
  return (
    <div className={`bg-gray-800/50 backdrop-blur-md border border-gray-700/30 rounded-lg overflow-hidden ${className}`}>
      <div className="animate-pulse">
        {/* Table Header */}
        <div className="bg-gray-800/80 p-4 border-b border-gray-700/30">
          <div className="grid grid-cols-4 gap-4">
            {Array.from({ length: cols }).map((_, index) => (
              <div key={index} className="h-5 bg-gray-700 rounded w-20"></div>
            ))}
          </div>
        </div>
        
        {/* Table Rows */}
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="p-4 border-b border-gray-700/30 last:border-b-0">
            <div className="grid grid-cols-4 gap-4">
              {Array.from({ length: cols }).map((_, colIndex) => (
                <div key={colIndex} className={`h-4 bg-gray-700 rounded ${
                  colIndex === 0 ? 'w-24' :
                  colIndex === 1 ? 'w-16' :
                  colIndex === 2 ? 'w-20' : 'w-12'
                }`}></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}