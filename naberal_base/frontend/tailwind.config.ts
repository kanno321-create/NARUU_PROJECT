import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                // Theme-aware colors using CSS variables
                brand: {
                    DEFAULT: "var(--color-brand)",
                    strong: "var(--color-brand-strong)",
                    subtle: "var(--color-brand-subtle)",
                },
                surface: {
                    DEFAULT: "var(--color-surface)",
                    secondary: "var(--color-surface-secondary)",
                    tertiary: "var(--color-surface-tertiary)",
                },
                text: {
                    DEFAULT: "var(--color-text)",
                    strong: "var(--color-text-strong)",
                    subtle: "var(--color-text-subtle)",
                },
                // Background color for theme
                bg: "var(--color-bg)",
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))",
                },
                destructive: {
                    DEFAULT: "hsl(var(--destructive))",
                    foreground: "hsl(var(--destructive-foreground))",
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))",
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))",
                },
                popover: {
                    DEFAULT: "hsl(var(--popover))",
                    foreground: "hsl(var(--popover-foreground))",
                },
                card: {
                    DEFAULT: "hsl(var(--card))",
                    foreground: "hsl(var(--card-foreground))",
                },
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
            },
            keyframes: {
                "accordion-down": {
                    from: { height: "0" },
                    to: { height: "var(--radix-accordion-content-height)" },
                },
                "accordion-up": {
                    from: { height: "var(--radix-accordion-content-height)" },
                    to: { height: "0" },
                },
                pulse: {
                    "0%, 100%": { opacity: "1" },
                    "50%": { opacity: "0.5" },
                },
                "fade-in": {
                    "0%": { opacity: "0", transform: "translateY(10px)" },
                    "100%": { opacity: "1", transform: "translateY(0)" },
                },
                "fade-in-up": {
                    "0%": { opacity: "0", transform: "translateY(20px)" },
                    "100%": { opacity: "1", transform: "translateY(0)" },
                },
                "slide-in-right": {
                    "0%": { opacity: "0", transform: "translateX(20px)" },
                    "100%": { opacity: "1", transform: "translateX(0)" },
                },
                "scale-in": {
                    "0%": { opacity: "0", transform: "scale(0.95)" },
                    "100%": { opacity: "1", transform: "scale(1)" },
                },
                "shimmer": {
                    "0%": { backgroundPosition: "-200% 0" },
                    "100%": { backgroundPosition: "200% 0" },
                },
                "glow": {
                    "0%, 100%": { boxShadow: "0 0 5px rgba(59, 130, 246, 0.5)" },
                    "50%": { boxShadow: "0 0 20px rgba(59, 130, 246, 0.8)" },
                },
                "float": {
                    "0%, 100%": { transform: "translateY(0)" },
                    "50%": { transform: "translateY(-5px)" },
                },
                "number-count": {
                    "0%": { opacity: "0", transform: "translateY(10px)" },
                    "100%": { opacity: "1", transform: "translateY(0)" },
                },
                "progress-fill": {
                    "0%": { width: "0%" },
                    "100%": { width: "var(--progress-width)" },
                },
                "sparkline-draw": {
                    "0%": { strokeDashoffset: "1000" },
                    "100%": { strokeDashoffset: "0" },
                },
                "bounce-subtle": {
                    "0%, 100%": { transform: "translateY(0)" },
                    "50%": { transform: "translateY(-3px)" },
                },
                "wiggle": {
                    "0%, 100%": { transform: "rotate(-1deg)" },
                    "50%": { transform: "rotate(1deg)" },
                },
            },
            animation: {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
                pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                "fade-in": "fade-in 0.5s ease-out forwards",
                "fade-in-up": "fade-in-up 0.6s ease-out forwards",
                "slide-in-right": "slide-in-right 0.4s ease-out forwards",
                "scale-in": "scale-in 0.3s ease-out forwards",
                "shimmer": "shimmer 2s linear infinite",
                "glow": "glow 2s ease-in-out infinite",
                "float": "float 3s ease-in-out infinite",
                "number-count": "number-count 0.5s ease-out forwards",
                "progress-fill": "progress-fill 1s ease-out forwards",
                "sparkline-draw": "sparkline-draw 1.5s ease-out forwards",
                "bounce-subtle": "bounce-subtle 2s ease-in-out infinite",
                "wiggle": "wiggle 0.3s ease-in-out",
            },
        },
    },
    plugins: [],
};
export default config;
