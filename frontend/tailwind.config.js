import animate from 'tailwindcss-animate';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        studio: {
          canvas: '#F9FAFB',
          card: '#FFFFFF',
          subtle: '#F3F4F6',
          active: '#E5E7EB',
          placeholder: '#4B5563',
          border: '#E5E7EB',
          divider: '#F3F4F6',
        },
      },
      borderRadius: {
        dock: '24px',
        slot: '12px',
        menu: '16px',
        pill: '9999px',
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)',
        'tab-active': '0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04)',
        dropdown: '0 12px 24px -4px rgba(0, 0, 0, 0.08), 0 4px 8px -2px rgba(0, 0, 0, 0.04)',
        'floating-dock': '0 20px 32px -6px rgba(0, 0, 0, 0.12), 0 8px 16px -4px rgba(0, 0, 0, 0.05)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      animation: {
        in: 'fade-in 150ms ease-out, zoom-in-95 150ms ease-out',
        out: 'fade-out 150ms ease-in, zoom-out-95 150ms ease-in',
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'fade-in': { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        'fade-out': { '0%': { opacity: '1' }, '100%': { opacity: '0' } },
        'zoom-in-95': { '0%': { transform: 'scale(0.95)' }, '100%': { transform: 'scale(1)' } },
        'zoom-out-95': { '0%': { transform: 'scale(1)' }, '100%': { transform: 'scale(0.95)' } },
        'pulse-glow': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.6', transform: 'scale(0.98)' },
        },
      },
    },
  },
  plugins: [animate],
};
