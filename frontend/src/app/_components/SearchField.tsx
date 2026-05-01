"use client";

import { IconListSearch, IconX } from "@tabler/icons-react";
import {
  Button as AriaButton,
  Group as AriaGroup,
  Input as AriaInput,
  SearchField as AriaSearchField,
  type SearchFieldProps as AriaSearchFieldProps,
} from "react-aria-components";
import merge from "../_utils/merge";

export interface SearchFieldProps extends AriaSearchFieldProps {
  placeholder?: string;
}

export default function SearchField({
  className,
  placeholder,
  ...props
}: SearchFieldProps) {
  return (
    <AriaSearchField
      className={merge("group/field w-full text-sm font-normal", className)}
      {...props}
    >
      <AriaGroup
        className={merge(
          "flex h-8 items-center overflow-hidden rounded-md border border-border bg-background px-1.5",
          "data-[focus-within]:outline data-[focus-within]:outline-1 data-[focus-within]:outline-gold",
        )}
      >
        <IconListSearch aria-hidden className="size-4 stroke-tertiary" />
        <AriaInput
          placeholder={placeholder}
          className="min-w-0 flex-1 bg-background p-1.5 text-primary outline-none placeholder:text-tertiary [&::-webkit-search-cancel-button]:hidden"
        />
        <AriaButton className="group/button -m-1.5 p-1.5 group-data-[empty]/field:hidden">
          <IconX className="size-4 stroke-tertiary group-hover/button:stroke-secondary" />
        </AriaButton>
      </AriaGroup>
    </AriaSearchField>
  );
}
