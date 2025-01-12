import {
  Listbox,
  ListboxButton,
  ListboxOptions,
  ListboxOption,
} from "@headlessui/react";
import { IconChevronDown } from "@tabler/icons-react";
import { Dispatch, SetStateAction } from "react";

export interface SmallSelectorOption {
  id: number;
  name: string;
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
        <ListboxButton className="relative h-full w-fit pr-4 text-left text-xs font-medium text-zinc-500 underline decoration-zinc-300 underline-offset-4 hover:text-zinc-600 hover:decoration-zinc-400 data-[focus]:text-zinc-600 data-[open]:text-zinc-600 data-[focus]:decoration-zinc-600 data-[open]:decoration-zinc-400">
          {state.name}
          <IconChevronDown
            className="group pointer-events-none absolute right-0 top-1/2 size-3.5 -translate-y-[50%]"
            aria-hidden="true"
          />
        </ListboxButton>
        <ListboxOptions
          modal={false}
          anchor="bottom start"
          transition
          className="z-50 !max-h-60 w-fit rounded-md border bg-white py-1 transition duration-100 ease-in [--anchor-gap:10px] focus:outline-none data-[leave]:data-[closed]:opacity-0"
        >
          {options.map((option) => (
            <ListboxOption
              key={option.id}
              value={option}
              className="group flex cursor-pointer select-none flex-row items-center gap-2 pl-2 pr-4 text-zinc-500 data-[focus]:text-zinc-800"
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

export function MediumSelector({
  state,
  setState,
  options,
}: {
  state: string;
  setState: Dispatch<SetStateAction<string>>;
  options: string[];
}) {
  return (
    <div className="h-8 w-fit flex-shrink-0">
      <Listbox value={state} onChange={setState}>
        <ListboxButton className="relative h-full w-fit rounded-md pr-5 text-left text-sm font-medium text-zinc-500 hover:text-zinc-800 data-[focus]:text-zinc-800 data-[open]:text-zinc-800">
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
          className="z-50 w-fit rounded-md border bg-white py-1 transition duration-100 ease-in [--anchor-gap:4px] focus:outline-none data-[leave]:data-[closed]:opacity-0"
        >
          {options.map((option) => (
            <ListboxOption
              key={option}
              value={option}
              className="group flex cursor-pointer select-none flex-row items-center gap-2 pr-4 text-zinc-500 data-[focus]:text-zinc-800"
            >
              <div className="invisible flex select-none items-center justify-center pl-2 text-sm text-gold group-data-[selected]:visible">
                <div>•</div>
              </div>
              <div className="py-1 text-sm font-medium">{option}</div>
            </ListboxOption>
          ))}
        </ListboxOptions>
      </Listbox>
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
    <div className="h-8 w-fit">
      <Listbox value={state} onChange={setState}>
        <ListboxButton className="relative h-full w-fit rounded-md pr-5 text-left text-xl font-medium text-zinc-800 underline decoration-zinc-400 underline-offset-4 hover:opacity-75 sm:text-lg">
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
          className="z-50 rounded-md border bg-white py-1 transition duration-100 ease-in [--anchor-gap:4px] focus:outline-none data-[leave]:data-[closed]:opacity-0"
        >
          {options.map((option) => (
            <ListboxOption
              key={option}
              value={option}
              className="group flex cursor-pointer select-none flex-row items-center gap-2 pr-4 text-zinc-500 data-[focus]:text-zinc-800"
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
