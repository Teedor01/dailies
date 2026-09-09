/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },

        evidence: {
          observed: '#2563eb',      
          correlation: '#7c3aed',  
          hypothesis: '#d97706',    
          verified: '#16a34a',      
          rejected: '#dc2626',      
          error: '#71717a',         
        },
      },
    },
  },
  plugins: [],
};
