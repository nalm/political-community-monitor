/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fmkorea: "#2563EB",
        bobaedream: "#059669",
        theqoo: "#DB2777",
        damoang: "#4F46E5",
        ddanzi: "#D97706",
        itssa: "#7C3AED",
      }
    },
  },
  plugins: [],
}
