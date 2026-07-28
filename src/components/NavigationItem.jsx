import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';

/**
 * NavigationItem Component
 *
 * Individual navigation menu item with active state, hover effects, and theme support.
 * Can be used standalone or as a child of NavigationSection for nested items.
 * Supports both internal React Router links and external URLs.
 *
 * Props:
 * @param {string} name - Display name of the menu item
 * @param {string} href - Navigation path/route or external URL
 * @param {React.Component} icon - Heroicon component
 * @param {boolean} indent - Whether to indent (for sub-items, default: false)
 * @param {boolean} external - Whether link is external (opens in new tab, default: false)
 * @param {string} className - Additional CSS classes
 * @param {function} onClick - Optional click handler
 *
 * Usage Examples:
 * ```jsx
 * // Internal route
 * <NavigationItem
 *   name="Dashboard"
 *   href="/admin/"
 *   icon={HomeIcon}
 * />
 *
 * // External link
 * <NavigationItem
 *   name="Documentation"
 *   href="https://example.com"
 *   icon={DocumentIcon}
 *   external={true}
 * />
 *
 * // Nested item with indent
 * <NavigationSection title="System" icon={CogIcon}>
 *   <NavigationItem
 *     name="General Settings"
 *     href="/admin/settings"
 *     icon={CogIcon}
 *     indent={true}
 *   />
 * </NavigationSection>
 * ```
 */
export default function NavigationItem({
  name,
  href,
  icon: Icon,
  indent = false,
  external = false,
  className = '',
  onClick,
  collapsed = false
}) {
  const location = useLocation();
  const { currentTheme } = useTheme();
  const isActive = !external && location.pathname === href;

  // Theme-aware styling based on active state
  const linkClasses = `
    group flex items-center ${collapsed ? 'justify-center px-2' : 'px-3'} py-2 text-sm font-medium rounded-lg
    transition-all duration-200
    focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
    ${currentTheme === 'unicorn'
      ? 'focus-visible:ring-purple-400'
      : currentTheme === 'light'
      ? 'focus-visible:ring-blue-500'
      : 'focus-visible:ring-blue-400'
    }
    ${indent && !collapsed ? 'pl-11' : ''}
    ${isActive
      ? currentTheme === 'unicorn'
        ? 'bg-white/20 text-white shadow-lg backdrop-blur-sm border border-white/20'
        : currentTheme === 'light'
        ? 'bg-blue-100 text-blue-900'
        : 'bg-blue-900 text-blue-100'
      : currentTheme === 'unicorn'
        ? 'text-purple-200 hover:bg-white/10 hover:text-white'
        : currentTheme === 'light'
        ? 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
    }
    ${className}
  `;

  const iconClasses = `
    ${collapsed ? '' : 'mr-3'} flex-shrink-0 h-5 w-5 transition-colors duration-200
    ${isActive
      ? currentTheme === 'unicorn'
        ? 'text-yellow-400'
        : currentTheme === 'light'
        ? 'text-blue-600'
        : 'text-blue-400'
      : currentTheme === 'unicorn'
        ? 'text-purple-300 group-hover:text-yellow-300'
        : currentTheme === 'light'
        ? 'text-gray-400 group-hover:text-gray-600'
        : 'text-gray-400 group-hover:text-gray-300'
    }
  `;

  const handleClick = (e) => {
    if (onClick) {
      onClick(e);
    }
  };

  // Render external link as <a> tag
  if (external) {
    return (
      <a
        href={href}
        onClick={handleClick}
        className={linkClasses}
        target="_blank"
        rel="noopener noreferrer"
        title={collapsed ? name : ''}
      >
        {Icon && (
          <Icon
            className={iconClasses}
            aria-hidden="true"
          />
        )}
        {!collapsed && <span>{name}</span>}
      </a>
    );
  }

  // Render internal link with React Router
  return (
    <Link
      to={href}
      onClick={handleClick}
      className={linkClasses}
      aria-current={isActive ? 'page' : undefined}
      title={collapsed ? name : ''}
    >
      {Icon && (
        <Icon
          className={iconClasses}
          aria-hidden="true"
        />
      )}
      {!collapsed && <span>{name}</span>}
    </Link>
  );
}
