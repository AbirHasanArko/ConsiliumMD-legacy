/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        badge: {
          "evidence-gap-resolved": "#16a34a",
          "evidence-gap-checking": "#d97706",
          "judgment-call": "#2563eb",
          "under-review": "#dc2626",
        },
      },
    },
  },
  plugins: [],
};
