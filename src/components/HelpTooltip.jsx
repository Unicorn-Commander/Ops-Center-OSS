/**
 * HelpTooltip Component - Reusable contextual help icon with tooltip
 *
 * UPDATED: October 30, 2025
 * PURPOSE: Provides users with contextual information about confusing or technical features
 *
 * USAGE:
 * <HelpTooltip title="What is this?" content="Detailed explanation here" />
 *
 * Or with multi-line content:
 * <HelpTooltip
 *   title="Local Users"
 *   content={[
 *     "This shows system users inside the Docker container",
 *     "For application users, see User Management"
 *   ]}
 *   link={{ text: "Learn more", href: "/docs/user-guide#local-users" }}
 * />
 */

import React, { useState } from 'react';
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function HelpTooltip({
  title,
  content,
  link = null,
  position = 'top',
  iconSize = 'h-5 w-5',
  className = ''
}) {
  const [showTooltip, setShowTooltip] = useState(false);
  const { currentTheme } = useTheme();

  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2'
  };

  const arrowClasses = {
    top: 'top-full left-1/2 transform -translate-x-1/2',
    right: 'right-full top-1/2 transform -translate-y-1/2',
    bottom: 'bottom-full left-1/2 transform -translate-x-1/2',
    left: 'left-full top-1/2 transform -translate-y-1/2'
  };

  // Theme-aware colors
  const bgColor = currentTheme === 'unicorn'
    ? 'bg-purple-900/95 backdrop-blur-sm border border-purple-500/30'
    : currentTheme === 'light'
    ? 'bg-gray-900/95 backdrop-blur-sm'
    : 'bg-gray-800/95 backdrop-blur-sm';

  const iconColor = currentTheme === 'unicorn'
    ? 'text-purple-300 hover:text-purple-200'
    : currentTheme === 'light'
    ? 'text-gray-500 hover:text-gray-700'
    : 'text-gray-400 hover:text-gray-300';

  const arrowColor = currentTheme === 'unicorn'
    ? position === 'top' ? 'border-t-purple-900' :
      position === 'right' ? 'border-r-purple-900' :
      position === 'bottom' ? 'border-b-purple-900' :
      'border-l-purple-900'
    : position === 'top' ? 'border-t-gray-800' :
      position === 'right' ? 'border-r-gray-800' :
      position === 'bottom' ? 'border-b-gray-800' :
      'border-l-gray-800';

  // Format content (array or string)
  const formatContent = () => {
    if (Array.isArray(content)) {
      return content.map((line, index) => (
        <div key={index} className="mb-1.5 last:mb-0">
          {line}
        </div>
      ));
    }
    return content;
  };

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        type="button"
        className={`ml-1 transition-colors duration-200 ${iconColor}`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip(!showTooltip)}
        aria-label="Help information"
      >
        <QuestionMarkCircleIcon className={iconSize} />
      </button>

      {showTooltip && (
        <div className={`absolute z-50 ${positionClasses[position]} w-80`}>
          <div className={`${bgColor} text-white text-sm rounded-lg shadow-2xl p-4`}>
            {title && (
              <div className="font-semibold mb-2 text-base">{title}</div>
            )}
            <div className={`${currentTheme === 'unicorn' ? 'text-purple-100' : 'text-gray-200'}`}>
              {formatContent()}
            </div>
            {link && (
              <a
                href={link.href}
                className={`inline-block mt-3 text-sm font-medium underline ${
                  currentTheme === 'unicorn'
                    ? 'text-purple-300 hover:text-purple-200'
                    : 'text-blue-400 hover:text-blue-300'
                }`}
                onClick={() => setShowTooltip(false)}
              >
                {link.text}
              </a>
            )}
            <div
              className={`absolute w-0 h-0 border-8 border-transparent ${arrowClasses[position]} ${arrowColor}`}
              style={{
                borderStyle: 'solid',
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}