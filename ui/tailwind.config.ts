import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        content: {
          primary: "var(--color-content-primary)",
          secondary: "var(--color-content-secondary)",
          muted: "var(--color-content-muted)",
          inverse: "var(--color-content-inverse)",
          accent: "var(--color-content-accent)",
        },
        surface: {
          page: "var(--color-surface-page)",
          panel: "var(--color-surface-panel)",
          overlay: "var(--color-surface-overlay)",
          hover: "var(--color-surface-hover)",
          selected: "var(--color-surface-selected)",
          disabled: "var(--color-surface-disabled)",
        },
        edge: {
          base: "var(--color-edge-base)",
          weak: "var(--color-edge-weak)",
          accent: "var(--color-edge-accent)",
          focus: "var(--color-edge-focus)",
        },
        accent: {
          primary: "var(--color-accent-primary)",
          secondary: "var(--color-accent-secondary)",
          positive: "var(--color-accent-positive)",
          warning: "var(--color-accent-warning)",
          negative: "var(--color-accent-negative)",
        },
        tint: {
          positive: "var(--color-tint-positive)",
          warning: "var(--color-tint-warning)",
          negative: "var(--color-tint-negative)",
          neutral: "var(--color-tint-neutral)",
        },
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
      },
      spacing: {
        "t-1": "var(--space-1)",
        "t-2": "var(--space-2)",
        "t-3": "var(--space-3)",
        "t-4": "var(--space-4)",
        "t-6": "var(--space-6)",
        "t-8": "var(--space-8)",
      },
      fontSize: {
        caption: "var(--font-size-caption)",
        "body-sm": "var(--font-size-body-sm)",
        body: "var(--font-size-body)",
        "heading-sm": "var(--font-size-heading-sm)",
        heading: "var(--font-size-heading)",
        display: "var(--font-size-display)",
      },
      fontFamily: {
        theme: "var(--font-family-theme)",
      },
    },
  },
  plugins: [],
} satisfies Config;
