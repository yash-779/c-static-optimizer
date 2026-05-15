import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#080b12",
          secondary: "#0d1117",
          card: "#0d1424",
          hover: "#111827",
        },
        accent: {
          purple: "#a855f7",
          cyan: "#22d3ee",
          green: "#10b981",
          red: "#ef4444",
          amber: "#f59e0b",
          blue: "#3b82f6",
        },
        border: {
          dim: "#1e293b",
          bright: "#334155",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "Consolas", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(168,85,247,0.15)",
        "glow-cyan": "0 0 20px rgba(34,211,238,0.15)",
      },
    },
  },
  plugins: [],
};
export default config;
