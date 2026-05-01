import { cva } from "class-variance-authority";

export const buttonVariants = cva(
  [
    "flex cursor-pointer items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors",
    "focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
    "[&_svg:not([class*='size-'])]:size-4 [&_svg]:pointer-events-none [&_svg]:shrink-0",
  ],
  {
    variants: {
      variant: {
        primary: [
          "bg-title text-background",
          "hover:bg-subtitle focus:bg-subtitle",
        ],
        secondary: [
          "border border-tertiary text-secondary",
          "hover:border-primary hover:text-primary focus:border-primary focus:text-primary",
        ],
      },
    },
    defaultVariants: {
      variant: "primary",
    },
  },
);
