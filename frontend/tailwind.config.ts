import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "score-a": "#27AE60",
        "score-b": "#2ECC71",
        "score-c": "#F39C12",
        "score-d": "#E67E22",
        "score-f": "#C0392B",
        navy: "#1B3A5C",
        blue: "#2E75B6",
        bg: "#F7F9FA",
        text: "#2C3E50",
        border: "#E2E8F0",
        muted: "#94A3B8",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Geist Mono", "monospace"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
