import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

/**
 * NavigationSection Component
 *
 * A collapsible navigation section with header and child items.
 * Supports smooth expand/collapse transitions and theme-aware styling.
 *
 * Props:
 * @param {string} title - Section header text
 * @param {React.Component} icon - Heroicon component for section header
 * @param {boolean} defaultOpen - Whether section starts expanded (default: false)
 * @param {Function} onToggle - Optional callback when section is toggled
 * @param {React.ReactNode} children - Child navigation items
 * @param {string} className - Additional CSS classes
 *
 * Usage Example:
 * ```jsx
 * <NavigationSection
 *   title="System"
 *   icon={CogIcon}
 *   defaultOpen={true}
 *   onToggle={() => saveState('system', !isOpen)}
 * >
 *   <NavigationItem name="Settings" href="/admin/settings" icon={CogIcon} />
 *   <NavigationItem name="Security" href="/admin/security" icon={ShieldCheckIcon} />
 * </NavigationSection>
 * ```
 */
export default function NavigationSection({
  title,
  icon: Icon,
  defaultOpen = false,
  onToggle,
  children,
  className = '',
  collapsed = false
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const { currentTheme } = useTheme();

  // Sync local state with defaultOpen prop changes
  useEffect(() => {
    setIsOpen(defaultOpen);
  }, [defaultOpen]);

  const toggleOpen = () => {
    setIsOpen(!isOpen);
    if (onToggle) {
      onToggle();
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleOpen();
    }
  };

  // Theme-aware styling
  const sectionHeaderClasses = `
    group flex items-center justify-between w-full px-3 py-2 text-sm font-semibold rounded-lg
    transition-all duration-200 cursor-pointer
    ${currentTheme === 'unicorn'
      ? 'text-purple-200 hover:bg-white/10 hover:text-white'
      : currentTheme === 'light'
      ? 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
    }
  `;

  const iconClasses = `
    flex-shrink-0 h-5 w-5 transition-colors duration-200
    ${currentTheme === 'unicorn'
      ? 'text-purple-300 group-hover:text-yellow-300'
      : currentTheme === 'light'
      ? 'text-gray-500 group-hover:text-gray-700'
      : 'text-gray-400 group-hover:text-gray-300'
    }
  `;

  const chevronClasses = `
    flex-shrink-0 h-4 w-4 transition-all duration-200
    ${currentTheme === 'unicorn'
      ? 'text-purple-400'
      : currentTheme === 'light'
      ? 'text-gray-400'
      : 'text-gray-500'
    }
    ${isOpen ? 'transform rotate-0' : ''}
  `;

  // When sidebar is collapsed, render children directly without section wrapper
  if (collapsed) {
    return <>{children}</>;
  }

  return (
    <div className={`mb-1 ${className}`}>
      {/* Section Header */}
      <button
        onClick={toggleOpen}
        onKeyDown={handleKeyDown}
        className={sectionHeaderClasses}
        aria-expanded={isOpen}
        aria-label={`${isOpen ? 'Collapse' : 'Expand'} ${title} section`}
      >
        <div className="flex items-center gap-3">
          {Icon && <Icon className={iconClasses} aria-hidden="true" />}
          <span className="uppercase tracking-wider text-xs font-bold">{title}</span>
        </div>
        {isOpen ? (
          <ChevronDownIcon className={chevronClasses} aria-hidden="true" />
        ) : (
          <ChevronRightIcon className={chevronClasses} aria-hidden="true" />
        )}
      </button>

      {/* Collapsible Content */}
      <div
        className={`
          overflow-hidden transition-all duration-300 ease-in-out
          ${isOpen ? 'max-h-[2000px] opacity-100 mt-1' : 'max-h-0 opacity-0'}
        `}
        aria-hidden={!isOpen}
      >
        <div className="space-y-1">
          {children}
        </div>
      </div>
    </div>
  );
}
