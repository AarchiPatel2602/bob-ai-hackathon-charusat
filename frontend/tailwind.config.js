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
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0f62fe', // IBM Carbon Blue
          600: '#0043ce',
          700: '#002d9c',
          800: '#001d6c',
          900: '#001141',
        },
        dark: {
          900: '#0d1117',
          850: '#161b22',
          800: '#21262d',
          750: '#2d333b',
          700: '#30363d',
          600: '#484f58',
        }
      }
    },
  },
  plugins: [],
}
