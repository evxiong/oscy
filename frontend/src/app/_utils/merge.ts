import type { ClassValue } from "clsx";
import clsx from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      colors: [
        "gold",
        "primary",
        "secondary",
        "tertiary",
        "title",
        "subtitle",
        "underline",
        "border",
        "active",
        "hover",
        "overlay",
        "light",
        "background",
        "ring",
      ],
    },
  },
});

export default function merge(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
