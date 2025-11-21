/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // AUB Official Brand Colors
        aub: {
          red: {
            // Berytus Red (Primary)
            DEFAULT: '#840132',
            dark: '#6a0028',
            light: '#a0013d',
            pale: '#f5e5ea',
          },
          gray: {
            // Light Gray (Secondary)
            DEFAULT: '#808080',
            dark: '#666666',
            light: '#999999',
          },
          black: '#000000', // Black (Secondary)
          cream: '#faf8f3',
          beige: '#f5f1e8',
        },
        // Semantic Colors
        success: '#2e7d32',
        warning: '#f57c00',
        error: '#c62828',
        info: '#0277bd',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      boxShadow: {
        'aub': '0 2px 8px rgba(132, 1, 50, 0.1)',
        'aub-lg': '0 4px 16px rgba(132, 1, 50, 0.15)',
        'aub-xl': '0 8px 32px rgba(132, 1, 50, 0.2)',
      },
      borderRadius: {
        'aub': '8px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
