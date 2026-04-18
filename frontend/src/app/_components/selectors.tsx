import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
} from "@headlessui/react";
import { IconChevronDown } from "@tabler/icons-react";
import { Dispatch, SetStateAction } from "react";
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
  return (
    <div className="w-fit flex-shrink-0">
      <Listbox value={state} onChange={setState}>
        <ListboxButton className="relative h-full max-w-16 truncate pr-4 text-left text-xs font-medium leading-5 text-zinc-500 underline decoration-zinc-300 underline-offset-4 hover:text-zinc-600 hover:decoration-zinc-400 data-[focus]:text-zinc-600 data-[open]:text-zinc-600 data-[focus]:decoration-zinc-600 data-[open]:decoration-zinc-400 xs:w-fit xs:max-w-full">
          {state.name}
          <IconChevronDown
            className="group pointer-events-none absolute right-0 top-1/2 size-3.5 -translate-y-[50%]"
            aria-hidden="true"
          />
        </ListboxButton>
        <ListboxOptions
          modal={false}
          anchor="bottom end"
          transition
          className="z-50 !max-h-60 w-fit rounded-md border bg-white py-1 transition duration-100 ease-in [--anchor-gap:10px] focus:outline-none data-[leave]:data-[closed]:opacity-0"
        >
          {options.map((option) => (
            <ListboxOption
              key={option.id}
              value={option}
              disabled={option.disabled}
              className="group flex cursor-pointer select-none flex-row items-center gap-2 pl-2 pr-4 text-zinc-500 data-[focus]:text-zinc-800 data-[disabled]:opacity-50"
            >
              <div className="invisible flex select-none items-center justify-center text-sm text-gold group-data-[selected]:visible">
                <div>•</div>
              </div>
              <div className="flex-shrink-0 py-1 pr-2 text-right text-sm font-medium">
                {option.name}
              </div>
            </ListboxOption>
          ))}
        </ListboxOptions>
      </Listbox>
    </div>
  );
}

export function SmallSelectorAria({
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
  return (
    <div className="w-fit shrink-0">
      <AriaSelect
        value={state.id}
        onChange={(v) => setState(idToOption.get(v as number)!)}
      >
        <AriaButton
          className={merge(
            "relative max-w-16 truncate pr-4 text-left text-xs/5 font-medium text-secondary underline decoration-underline underline-offset-4 xs:w-fit xs:max-w-full",
            "hover:text-primary hover:decoration-tertiary data-[focus-visible]:text-primary data-[pressed]:text-primary data-[focus-visible]:decoration-primary data-[pressed]:decoration-tertiary",
          )}
        >
          <AriaSelectValue />
          <IconChevronDown className="pointer-events-none absolute right-0 top-1/2 size-3.5 -translate-y-1/2" />
        </AriaButton>
        <AriaPopover
          className="!max-h-60 overflow-y-auto rounded-md border border-border bg-white p-1 font-medium text-secondary drop-shadow-sm"
          placement="bottom end"
        >
          <AriaListBox>
            {options.map((option) => (
              <AriaListBoxItem
                key={option.id}
                id={option.id}
                textValue={option.name}
                isDisabled={option.disabled}
                className={merge(
                  "group relative cursor-default whitespace-nowrap rounded-sm text-sm",
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

      {/* <Listbox value={state} onChange={setState}>
        <ListboxButton className="relative h-full max-w-16 truncate pr-4 text-left text-xs font-medium leading-5 text-zinc-500 underline decoration-zinc-300 underline-offset-4 hover:text-zinc-600 hover:decoration-zinc-400 data-[focus]:text-zinc-600 data-[open]:text-zinc-600 data-[focus]:decoration-zinc-600 data-[open]:decoration-zinc-400 xs:w-fit xs:max-w-full">
          {state.name}
          <IconChevronDown
            className="group pointer-events-none absolute right-0 top-1/2 size-3.5 -translate-y-[50%]"
            aria-hidden="true"
          />
        </ListboxButton>
        <ListboxOptions
          modal={false}
          anchor="bottom end"
          transition
          className="z-50 !max-h-60 w-fit rounded-md border bg-white py-1 transition duration-100 ease-in [--anchor-gap:10px] focus:outline-none data-[leave]:data-[closed]:opacity-0"
        >
          {options.map((option) => (
            <ListboxOption
              key={option.id}
              value={option}
              disabled={option.disabled}
              className="group flex cursor-pointer select-none flex-row items-center gap-2 pl-2 pr-4 text-zinc-500 data-[focus]:text-zinc-800 data-[disabled]:opacity-50"
            >
              <div className="invisible flex select-none items-center justify-center text-sm text-gold group-data-[selected]:visible">
                <div>•</div>
              </div>
              <div className="flex-shrink-0 py-1 pr-2 text-right text-sm font-medium">
                {option.name}
              </div>
            </ListboxOption>
          ))}
        </ListboxOptions>
      </Listbox> */}
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
  return (
    <div className="h-8 w-fit flex-shrink-0">
      {/* @ts-expect-error: isKey is always key of state as string */}
      <Listbox value={state} by={idKey} onChange={setState}>
        <ListboxButton className="relative h-full max-w-40 truncate rounded-md pr-5 text-left text-sm font-medium text-zinc-500 hover:text-zinc-800 focus:outline-none data-[focus]:text-zinc-800 data-[open]:text-zinc-800 xs:w-fit xs:max-w-full">
          {state[displayKey] as string}
          <IconChevronDown
            className="group pointer-events-none absolute right-0 top-1/2 size-4 -translate-y-[50%]"
            aria-hidden="true"
          />
        </ListboxButton>
        <ListboxOptions
          modal={false}
          anchor="bottom start"
          transition
          className="z-50 w-fit rounded-md border bg-white py-1 transition duration-100 ease-in [--anchor-gap:4px] focus:outline-none data-[leave]:data-[closed]:opacity-0"
        >
          {options.map((option) => (
            <ListboxOption
              key={option[idKey] as string}
              value={option}
              className="group flex cursor-pointer select-none flex-row items-center gap-2 pr-4 text-zinc-500 data-[focus]:text-zinc-800"
            >
              <div className="invisible flex select-none items-center justify-center pl-2 text-sm text-gold group-data-[selected]:visible">
                <div>•</div>
              </div>
              <div className="py-1 text-sm font-medium">
                {option[displayKey] as string}
              </div>
            </ListboxOption>
          ))}
        </ListboxOptions>
      </Listbox>
    </div>
  );
}

export function MediumSelectorAria<T>({
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
        <AriaPopover className="overflow-hidden rounded-md border border-border bg-white p-1 font-medium text-secondary drop-shadow-sm">
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

export function LargeSelector({
  state,
  setState,
  options,
}: {
  state: string;
  setState: Dispatch<SetStateAction<string>>;
  options: string[];
}) {
  return (
    <div className="h-8">
      <Listbox value={state} onChange={setState}>
        <ListboxButton className="relative h-full rounded-md pr-5 text-left text-xl font-medium text-primary underline decoration-zinc-400 underline-offset-4 hover:opacity-75 focus:opacity-75 sm:text-lg">
          {state}
          <IconChevronDown
            className="group pointer-events-none absolute right-0 top-1/2 size-4 -translate-y-[50%]"
            aria-hidden="true"
          />
        </ListboxButton>
        <ListboxOptions
          modal={false}
          anchor="bottom start"
          transition
          className="z-50 rounded-md border bg-background py-1 transition duration-100 ease-in [--anchor-gap:4px] focus:outline-none data-[leave]:data-[closed]:opacity-0"
        >
          {options.map((option) => (
            <ListboxOption
              key={option}
              value={option}
              className="group flex cursor-pointer select-none flex-row items-center gap-2 pr-4 text-secondary data-[focus]:text-primary"
            >
              <div className="invisible flex select-none items-center justify-center pl-2 text-sm text-gold group-data-[selected]:visible">
                <div>•</div>
              </div>
              <div className="py-1 text-sm font-medium data-[focus]:underline">
                {option}
              </div>
            </ListboxOption>
          ))}
        </ListboxOptions>
      </Listbox>
    </div>
  );
}
