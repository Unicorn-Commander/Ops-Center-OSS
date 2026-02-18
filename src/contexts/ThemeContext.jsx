import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Theme configurations
// Updated with WCAG AA compliant color choices for better accessibility
const themes = {
  dark: {
    name: 'Professional Dark',
    id: 'dark',
    primary: 'blue-500',
    accent: 'cyan-400',
    background: 'bg-gradient-to-br from-slate-900 via-slate-800 to-gray-900',
    sidebar: 'bg-slate-800/95 backdrop-blur-lg border-r border-slate-700/50 shadow-2xl',
    card: 'bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 shadow-xl',
    button: 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg',
    text: {
      primary: 'text-white',           // 17.85:1 on background ✅ AAA
      secondary: 'text-slate-300',     // 12.02:1 on background ✅ AAA
      accent: 'text-cyan-400',         // 9.88:1 on background ✅ AAA
      logo: 'text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400'
    },
    status: {
      success: 'text-emerald-400',     // 9.29:1 ✅ AAA
      warning: 'text-amber-400',       // 10.69:1 ✅ AAA
      error: 'text-red-500',           // 4.77:1 ✅ AA (FIXED: was red-600 at 3.70:1)
      info: 'text-blue-400'            // 7.02:1 ✅ AAA
    }
  },
  light: {
    name: 'Professional Light',
    id: 'light',
    primary: 'blue-600',
    accent: 'sky-500',
    background: 'bg-gradient-to-br from-gray-50 via-white to-blue-50',
    sidebar: 'bg-white/95 backdrop-blur-lg border-r border-gray-200 shadow-xl',
    card: 'bg-white border border-gray-200 shadow-lg',
    button: 'bg-blue-600 hover:bg-blue-700 text-white shadow-md',
    text: {
      primary: 'text-gray-900',        // 17.74:1 on background ✅ AAA
      secondary: 'text-gray-600',      // 7.56:1 on background ✅ AAA
      accent: 'text-blue-600',         // 5.17:1 on background ✅ AA
      logo: 'text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-sky-500'
    },
    status: {
      success: 'text-green-700',       // 4.67:1 ✅ AA (FIXED: was emerald-400 at 1.92:1)
      warning: 'text-amber-700',       // 4.51:1 ✅ AA (FIXED: was amber-400 at 1.67:1)
      error: 'text-red-700',           // 5.07:1 ✅ AA (FIXED: was rose-400 at 2.69:1)
      info: 'text-blue-700'            // 6.70:1 ✅ AAA (FIXED: was blue-400 at 2.54:1)
    }
  },
  unicorn: {
    name: 'Magic Unicorn',
    id: 'unicorn',
    primary: 'purple-500',
    accent: 'violet-400',
    background: 'bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900',
    sidebar: 'bg-slate-900/95 backdrop-blur-xl border-r border-purple-500/10',
    card: 'bg-slate-800/80 backdrop-blur-md border border-purple-500/10 shadow-lg hover:shadow-purple-500/5', // Increased opacity from 50% to 80%
    button: 'bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-700 hover:to-violet-700 text-white shadow-lg shadow-purple-500/20',
    text: {
      primary: 'text-gray-100',        // 16.22:1 on background ✅ AAA
      secondary: 'text-gray-400',      // 7.03:1 on background ✅ AAA
      accent: 'text-violet-300',       // 8.95:1 on background ✅ AAA (ENHANCED: was violet-400 at 6.56:1)
      logo: 'text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-violet-400 to-indigo-400'
    },
    status: {
      success: 'text-emerald-400',     // 9.29:1 ✅ AAA
      warning: 'text-amber-400',       // 10.69:1 ✅ AAA
      error: 'text-red-500',           // 4.77:1 ✅ AA (FIXED: was rose-400/red-600)
      info: 'text-sky-400'             // 8.48:1 ✅ AAA
    }
  },
  galaxy: {
    name: 'Unicorn Galaxy',
    id: 'galaxy',
    primary: 'purple-600',
    accent: 'yellow-400',
    background: 'galaxy-bg', // Custom CSS class for animated gradient
    sidebar: 'glass-card backdrop-blur-xl border-r border-white/10',
    card: 'glass-card backdrop-blur-md border border-white/10 shadow-2xl card-glow',
    button: 'bg-gradient-to-r from-purple-600 via-violet-600 to-purple-600 hover:from-purple-700 hover:via-violet-700 hover:to-purple-700 text-white shadow-lg shadow-purple-500/30',
    text: {
      primary: 'text-white',           // Should be AAA on dark backgrounds
      secondary: 'text-white/70',      // 70% opacity for secondary text
      accent: 'text-yellow-400',       // Bright accent for visibility
      logo: 'gold-text font-space'     // Custom CSS class for gold gradient
    },
    status: {
      success: 'text-emerald-400',     // Bright colors for animated background
      warning: 'text-amber-400',
      error: 'text-red-500',           // FIXED: consistent with other themes
      info: 'text-sky-400'
    },
    // Galaxy-specific properties
    useBackgroundEffects: true, // Flag to enable BackgroundEffects component
    fonts: {
      body: 'font-poppins',
      display: 'font-space'
    }
  },
  underground: {
    name: 'Special Projects',
    id: 'underground',
    primary: 'purple-700',
    accent: 'fuchsia-500',
    background: 'bg-gradient-to-br from-black via-purple-950 to-slate-950',
    sidebar: 'bg-black/95 backdrop-blur-xl border-r border-purple-900/50',
    card: 'bg-purple-950/80 backdrop-blur-md border border-purple-800/30 shadow-xl shadow-purple-900/20',
    button: 'bg-gradient-to-r from-purple-700 to-fuchsia-700 hover:from-purple-800 hover:to-fuchsia-800 text-white shadow-lg shadow-purple-900/40',
    text: {
      primary: 'text-white',
      secondary: 'text-purple-300',
      accent: 'text-fuchsia-400',
      logo: 'text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-fuchsia-400 to-pink-400'
    },
    status: {
      success: 'text-emerald-400',
      warning: 'text-amber-400',
      error: 'text-red-500',
      info: 'text-cyan-400'
    }
  }
};

/**
 * ACCESSIBILITY IMPROVEMENTS (October 19, 2025)
 *
 * Changes made to meet WCAG 2.1 Level AA standards:
 *
 * 1. Dark Theme:
 *    - Changed error color from red-600 (3.70:1) to red-500 (4.77:1)
 *    - Now all status colors pass WCAG AA (>4.5:1)
 *
 * 2. Light Theme:
 *    - Changed success from emerald-400 (1.92:1) to green-700 (4.67:1)
 *    - Changed warning from amber-400 (1.67:1) to amber-700 (4.51:1)
 *    - Changed error from rose-400 (2.69:1) to red-700 (5.07:1)
 *    - Changed info from blue-400 (2.54:1) to blue-700 (6.70:1)
 *    - All status colors now meet WCAG AA minimum (4.5:1)
 *
 * 3. Unicorn Theme:
 *    - Enhanced accent from violet-400 (6.56:1 AA) to violet-300 (8.95:1 AAA)
 *    - Changed error from red-600 to red-500 for consistency
 *    - Increased card opacity from 50% to 80% for better text contrast
 *
 * 4. Galaxy Theme:
 *    - Changed error from red-600 to red-500 for consistency
 *
 * All themes now achieve 100% WCAG AA compliance for tested color combinations.
 *
 * Contrast ratios verified with WCAG 2.1 relative luminance formula.
 * See /docs/UI_CONTRAST_AUDIT.md for complete audit report.
 */

export function ThemeProvider({ children }) {
  const [currentTheme, setCurrentTheme] = useState('underground'); // Default to Underground theme for your-domain.com
  const [isDarkMode, setIsDarkMode] = useState(true);

  useEffect(() => {
    // Apply theme to document
    const theme = themes[currentTheme];

    // For light theme, ensure dark mode is off
    if (currentTheme === 'light') {
      document.documentElement.classList.remove('dark');
    } else {
      document.documentElement.classList.add('dark');
    }

    // Store theme preference
    localStorage.setItem('uc1-theme', currentTheme);
  }, [currentTheme]);

  useEffect(() => {
    // Load saved theme
    const savedTheme = localStorage.getItem('uc1-theme');
    const savedDarkMode = localStorage.getItem('uc1-dark-mode');

    if (savedTheme && themes[savedTheme]) {
      setCurrentTheme(savedTheme);
    }
    if (savedDarkMode !== null) {
      setIsDarkMode(savedDarkMode === 'true');
    }
  }, []);

  const switchTheme = (themeName) => {
    if (themes[themeName]) {
      setCurrentTheme(themeName);
    }
  };

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const value = {
    currentTheme,
    theme: themes[currentTheme],
    availableThemes: Object.keys(themes),
    switchTheme,
    isDarkMode,
    toggleDarkMode,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}
