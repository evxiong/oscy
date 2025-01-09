import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-albert-sans)"],
      },
      fontSize: {
        xxs: ["0.625rem", "0.75rem"],
      },
      colors: {
        gold: "#B59349",
      },
    },
  },
  plugins: [],
} satisfies Config;
