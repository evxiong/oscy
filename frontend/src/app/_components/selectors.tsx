"use client";

import { IconChevronDown } from "@tabler/icons-react";
import { Dispatch, SetStateAction, useEffect, useRef, useState } from "react";
import {
  Button as AriaButton,
  ListBox as AriaListBox,
  ListBoxItem as AriaListBoxItem,
  Popover as AriaPopover,
  Select as AriaSelect,
  SelectValue as AriaSelectValue,
} from "react-aria-components";
import merge from "../_utils/merge";

export interface SmallSelectorOption {
  id: number;
  name: string;
  disabled: boolean;
}

export function SmallSelector({
  state,
  setState,
  options,
}: {
  state: SmallSelectorOption;
  setState: Dispatch<SetStateAction<SmallSelectorOption>>;
  options: SmallSelectorOption[];
}) {
  // map of each option's id to the option itself
  const idToOption = new Map(options.map((option) => [option.id, option]));

  const [open, setOpen] = useState(false);
  const listBoxRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!listBoxRef.current) {
      return;
    }
    const option = listBoxRef.current.querySelector(
      "div[data-selected='true']",
    );
    if (option) {
      option.scrollIntoView({ block: "nearest" });
    }
  }, [open]);

  return (
    <div className="w-fit shrink-0">
      <AriaSelect
        value={state.id}
        onChange={(v) => setState(idToOption.get(v as number)!)}
        isOpen={open}
        onOpenChange={setOpen}
      >
        <AriaButton
          className={merge(
            "relative max-w-16 truncate pr-4 text-left text-xs/5 font-medium text-secondary underline decoration-underline underline-offset-4 xs:w-fit xs:max-w-full",
            "hover:text-primary hover:decoration-tertiary data-[focus-visible]:text-primary data-[pressed]:text-primary data-[focus-visible]:decoration-primary data-[pressed]:decoration-gold",
          )}
        >
          <AriaSelectValue />
          <IconChevronDown className="pointer-events-none absolute right-0 top-1/2 size-3.5 -translate-y-1/2" />
        </AriaButton>
        <AriaPopover
          className="rounded-md border border-border bg-background font-medium text-secondary drop-shadow-sm transition-opacity data-[entering]:opacity-0"
          placement="bottom end"
        >
          <AriaListBox
            ref={(v) => {
              listBoxRef.current = v;
            }}
            className="max-h-60 w-fit scroll-pb-1 overflow-y-auto p-1"
          >
            {options.map((option) => (
              <AriaListBoxItem
                key={option.id}
                id={option.id}
                textValue={option.name}
                isDisabled={option.disabled}
                className={merge(
                  "group relative cursor-default rounded-sm text-sm",
                  "data-[selection-mode]:py-1 data-[selection-mode]:pl-5 data-[selection-mode]:pr-5",
                  option.disabled
                    ? "data-[disabled]:cursor-not-allowed data-[disabled]:text-tertiary"
                    : "hover:bg-hover hover:text-primary data-[focused]:bg-hover data-[focused]:text-primary",
                )}
              >
                <div className="absolute left-2 top-1/2 hidden size-[5px] -translate-y-1/2 rounded-full bg-gold group-data-[selected]:block"></div>
                <span>{option.name}</span>
              </AriaListBoxItem>
            ))}
          </AriaListBox>
        </AriaPopover>
      </AriaSelect>
    </div>
  );
}

export function MediumSelector<T>({
  state,
  setState,
  options,
  idKey,
  displayKey,
}: {
  state: T;
  setState: Dispatch<SetStateAction<T>>;
  options: T[];
  idKey: keyof T;
  displayKey: keyof T;
}) {
  // map of each option's id to the option itself
  const idToOption = new Map(
    options.map((option) => [option[idKey] as string, option]),
  );
  return (
    <div className="w-fit shrink-0">
      <AriaSelect
        value={state[idKey] as string}
        onChange={(v) => setState(idToOption.get(v as string)!)}
      >
        <AriaButton
          className={merge(
            "flex h-8 flex-row items-center gap-1 whitespace-nowrap rounded-md border border-border px-2 text-sm font-medium text-secondary",
            "data-[focus-visible]:text-primary data-[hovered]:text-primary data-[pressed]:text-primary data-[pressed]:outline data-[pressed]:outline-1 data-[pressed]:outline-gold",
          )}
        >
          <AriaSelectValue />
          <IconChevronDown className="size-3.5" />
        </AriaButton>
        <AriaPopover className="overflow-hidden rounded-md border border-border bg-background p-1 font-medium text-secondary drop-shadow-sm transition-opacity data-[entering]:opacity-0">
          <AriaListBox>
            {options.map((option) => (
              <AriaListBoxItem
                key={option[idKey] as string}
                id={option[idKey] as string}
                textValue={option[displayKey] as string}
                className="group relative cursor-default rounded-sm text-sm data-[focused]:bg-hover data-[hovered]:bg-hover data-[selection-mode]:py-1 data-[selection-mode]:pl-5 data-[selection-mode]:pr-4 data-[focused]:text-primary data-[hovered]:text-primary"
              >
                <div className="absolute left-2 top-1/2 hidden size-[5px] -translate-y-1/2 rounded-full bg-gold group-data-[selected]:block"></div>
                <span>{option[displayKey] as string}</span>
              </AriaListBoxItem>
            ))}
          </AriaListBox>
        </AriaPopover>
      </AriaSelect>
    </div>
  );
}
