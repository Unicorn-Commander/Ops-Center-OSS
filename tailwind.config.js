/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Unicorn Commander Brand Colors
        primary: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7c3aed',
          800: '#6b21a8',
          900: '#581c87',
          950: '#3b0764',
        },
        unicorn: {
          purple: '#b66eff',
          blue: '#00d4ff',
          gold: '#ffab00',
          green: '#00e676',
          red: '#ff5252',
          rainbow: {
            red: '#ff00cc',
            blue: '#3333ff',
            cyan: '#00ccff',
            orange: '#ff6600',
            purple: '#cc00ff',
            green: '#00ff99',
            pink: '#ff0066',
          }
        },
        commander: {
          navy: '#1e3a8a',
          gold: '#d97706',
          silver: '#6b7280',
        },
        // Galaxy Theme Colors
        'uc-deep-purple': '#1a0033',
        'uc-dark-purple': '#220044',
        'uc-blue-black': '#0a1929',
        'uc-purple-magenta': '#3a0e5a',
        'uc-gold': '#ffd700',
        'uc-yellow-gold': '#ffed4e',
        'uc-orange-gold': '#ffb700',
      },
      fontFamily: {
        'poppins': ['Poppins', 'sans-serif'],
        'space': ['Space Grotesk', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'galaxy-shift': 'galaxyShift 20s ease infinite',
        'status-pulse': 'statusPulse 2s infinite',
        'twinkle': 'twinkle 3s infinite',
        'float-star': 'floatStar 20s linear infinite',
        'neural-pulse': 'neuralPulse 4s infinite',
        'connection-flow': 'connectionFlow 3s infinite',
      },
      keyframes: {
        galaxyShift: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        statusPulse: {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.2)', opacity: '0.7' },
        },
        twinkle: {
          '0%, 100%': { opacity: '0', transform: 'scale(0.8)' },
          '50%': { opacity: '1', transform: 'scale(1)' },
        },
        floatStar: {
          'from': { transform: 'translateX(-100px)' },
          'to': { transform: 'translateX(calc(100vw + 100px))' },
        },
        neuralPulse: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.5' },
          '50%': { transform: 'scale(1.5)', opacity: '1' },
        },
        connectionFlow: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      backdropBlur: {
        'xl': '20px',
      },
      backdropSaturate: {
        '180': '180%',
      },
    },
  },
  plugins: [],
}