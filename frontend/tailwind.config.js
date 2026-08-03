/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#0A1628",
        cardbg: "#0D1E35",
        borderc: "#1A3050",
        accent: "#3B82F6",
      },
    },
  },
  plugins: [],
};
