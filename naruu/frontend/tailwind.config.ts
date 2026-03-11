import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        naruu: {
          50: "#f0f7ff",
          100: "#e0effe",
          200: "#baddfd",
          300: "#7dc2fc",
          400: "#38a3f8",
          500: "#0e87e9",
          600: "#026bc7",
          700: "#0355a1",
          800: "#074985",
          900: "#0c3d6e",
          950: "#082749",
        },
      },
    },
  },
  plugins: [],
};

export default config;
