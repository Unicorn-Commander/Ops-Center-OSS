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
      primary: 'text-white',
      secondary: 'text-slate-300',
      accent: 'text-cyan-400',
      logo: 'text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400'
    },
    status: {
      success: 'text-emerald-400',
      warning: 'text-amber-400',
      error: 'text-rose-400',
      info: 'text-blue-400'
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
      primary: 'text-gray-900',
      secondary: 'text-gray-600',
      accent: 'text-blue-600',
      logo: 'text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-sky-500'
    },
    status: {
      success: 'text-green-600',
      warning: 'text-orange-600',
      error: 'text-red-600',
      info: 'text-blue-600'
    }
  },
  unicorn: {
    name: 'Magic Unicorn',
    id: 'unicorn',
    primary: 'purple-500',
    accent: 'yellow-400',
    background: 'bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900',
    sidebar: 'bg-gradient-to-b from-purple-900/95 via-blue-900/95 to-indigo-900/95 backdrop-blur-lg border-r border-white/20',
    card: 'bg-gradient-to-br from-purple-800/60 via-purple-700/50 to-indigo-800/60 backdrop-blur-lg border border-purple-400/30 shadow-xl',
    button: 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg',
    text: {
      primary: 'text-white',
      secondary: 'text-purple-200',
      accent: 'text-yellow-300',
      logo: 'text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-purple-400 to-indigo-400'
    },
    status: {
      success: 'text-emerald-400',
      warning: 'text-yellow-400',
      error: 'text-rose-400',
      info: 'text-cyan-400'
    }
  }
};

export function ThemeProvider({ children }) {
  const [currentTheme, setCurrentTheme] = useState('unicorn'); // Default to Magic Unicorn theme
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