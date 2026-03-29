/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        heading: ['"Space Grotesk"', 'sans-serif'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#ecfeff',
          100: '#cffafe',
          500: '#06b6d4',
          700: '#0e7490',
          900: '#164e63'
        }
      },
      boxShadow: {
        focus: '0 0 0 3px rgba(6, 182, 212, 0.2)',
      }
    },
  },
  plugins: [],
};
