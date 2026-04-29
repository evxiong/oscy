import { type VariantProps } from "class-variance-authority";
import {
  Button as AriaButton,
  type ButtonProps as AriaButtonProps,
} from "react-aria-components";
import merge from "../_utils/merge";
import { buttonVariants } from "./variants";

interface ButtonProps
  extends AriaButtonProps,
    VariantProps<typeof buttonVariants> {}

export default function Button({ className, variant, ...props }: ButtonProps) {
  return (
    <AriaButton
      className={merge(buttonVariants({ variant, className }))}
      {...props}
    />
  );
}
