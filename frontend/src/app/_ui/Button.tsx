"use client";

import {
  Button as AriaButton,
  type ButtonProps as AriaButtonProps,
} from "react-aria-components";
import merge from "../_utils/merge";

export default function Button({ className, ...props }: AriaButtonProps) {
  return (
    <AriaButton
      className={merge(
        "flex cursor-pointer flex-row items-center gap-2 rounded-md border border-border-active px-4 py-2 text-sm font-medium text-secondary",
        "hover:border-primary hover:text-primary focus:border-primary focus:text-primary focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold",
        className,
      )}
      {...props}
    />
  );
}
