import React, { useState } from 'react';

/**
 * Reusable collapsible section component for unified LLM Management page
 *
 * @param {string} title - Section title
 * @param {string} status - Section status: 'success', 'warning', 'error', 'info', or null
 * @param {string} statusMessage - Optional message to display next to status indicator
 * @param {boolean} defaultExpanded - Whether section starts expanded (default: true)
 * @param {object} theme - Optional theme object for styling
 * @param {React.ReactNode} children - Section content
 */
export default function CollapsibleSection({
  title,
  status = null,
  statusMessage = '',
  defaultExpanded = true,
  theme = null,
  children
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // Status badge mapping
  const statusConfig = {
    success: { icon: '✅', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30' },
    warning: { icon: '⚠️', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
    error: { icon: '❌', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' },
    info: { icon: '🔵', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30' }
  };

  const currentStatus = status ? statusConfig[status] : null;

  // Theme fallbacks for null safety
  const cardBg = theme?.card || 'bg-gray-800';
  const borderColor = theme?.border || 'border-gray-700';
  const textPrimary = theme?.text?.primary || 'text-white';
  const textSecondary = theme?.text?.secondary || 'text-gray-400';
  const hoverBg = theme?.hover?.bg || 'hover:bg-gray-700/50';

  return (
    <div className={`${cardBg} rounded-xl border ${borderColor} overflow-hidden transition-all duration-300`}>
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-full px-6 py-4 flex items-center justify-between ${hoverBg} transition-colors duration-200`}
      >
        {/* Left side: Title and status */}
        <div className="flex items-center gap-4">
          <h3 className={`text-lg font-semibold ${textPrimary}`}>
            {title}
          </h3>

          {/* Status badge */}
          {currentStatus && (
            <div className={`flex items-center gap-2 px-3 py-1 rounded-lg border ${currentStatus.bg} ${currentStatus.border}`}>
              <span className="text-sm">{currentStatus.icon}</span>
              {statusMessage && (
                <span className={`text-sm font-medium ${currentStatus.color}`}>
                  {statusMessage}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Right side: Expand/collapse icon */}
        <div className={`transition-transform duration-300 ${isExpanded ? 'rotate-180' : 'rotate-0'}`}>
          <svg
            className={`w-5 h-5 ${textSecondary}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </button>

      {/* Body - with smooth CSS transition */}
      <div
        className={`transition-all duration-300 ease-in-out overflow-hidden ${
          isExpanded ? 'max-h-[5000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className={`px-6 py-4 border-t ${borderColor}`}>
          {children}
        </div>
      </div>
    </div>
  );
}
