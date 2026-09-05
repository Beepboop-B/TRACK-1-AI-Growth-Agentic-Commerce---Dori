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
        darkBg: '#0D0B08',
        darkSurface: '#15120E',
        darkSurfaceEl: '#1B1712',
        darkBorder: 'rgba(243,233,213,0.10)',
        darkText1: '#F3E9D5',
        darkText2: '#A99B88',
        darkText3: '#6E6355',
        amber: '#D99A3D',
        amberSoft: 'rgba(217,154,61,0.14)',
        green: '#35C978',
        greenSoft: 'rgba(53,201,120,0.12)',
        red: '#E85D5D',
        redSoft: 'rgba(232,93,93,0.12)',

        lightBg: '#F5F1E8',
        lightSurface: '#FFFFFF',
        lightSurfaceEl: '#FFFDF8',
        lightBorder: 'rgba(25,20,15,0.08)',
        lightText1: '#17130F',
        lightText2: '#6F675D',
        lightText3: '#9E9588',
        lightAmber: '#D99024',
        lightAmberSoft: 'rgba(217,144,36,0.10)',
        lightGreen: '#20A866',
        lightGreenSoft: 'rgba(32,168,102,0.10)',
        lightRed: '#D94B4B',
        lightRedSoft: 'rgba(217,75,75,0.10)',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
