import type { Config } from "tailwindcss";
import colors from "tailwindcss/colors";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      screens: {
        xxs: "360px",
        xs: "480px",
      },
      fontFamily: {
        sans: ["var(--font-figtree)"],
      },
      fontSize: {
        xxs: ["0.625rem", "0.75rem"],
      },
      colors: {
        gold: "#B59349",
        primary: colors.zinc[800],
        secondary: colors.zinc[500],
        tertiary: colors.zinc[400],
        title: colors.zinc[700],
        subtitle: colors.zinc[600],
        underline: colors.zinc[300],
        "border-active": colors.zinc[300],
        border: colors.zinc[200],
        "border-light": colors.zinc[100],
        active: colors.zinc[200],
        hover: colors.zinc[100],
        overlay: colors.zinc[100],
        light: colors.zinc[50],
        background: colors.white,
        ring: colors.blue[600],
      },
    },
  },
  plugins: [],
} satisfies Config;
