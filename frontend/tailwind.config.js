/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0B0F14",
        surface: "#131820",
        surface2: "#1A2029",
        border: "#232B36",
        text: "#E6EDF3",
        muted: "#7C8894",
        accent: "#4FD1C5",
        risk: {
          critical: "#F87171",
          high: "#FB923C",
          medium: "#FBBF24",
          low: "#34D399",
        },
        node: {
          module: "#6366f1",
          service: "#0ea5e9",
          database: "#16a34a",
          cache: "#dc2626",
          queue: "#d97706",
          external_api: "#9333ea",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      keyframes: {
        pulseglow: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(79, 209, 197, 0.4)" },
          "50%": { boxShadow: "0 0 0 8px rgba(79, 209, 197, 0)" },
        },
      },
      animation: {
        pulseglow: "pulseglow 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
