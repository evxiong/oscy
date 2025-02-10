"use client";

import { Button } from "@headlessui/react";
import { SearchRefContext } from "./searchRefContext";
import { useContext } from "react";
import { IconSearch } from "@tabler/icons-react";

export default function ExploreButton({
  id,
  text,
}: {
  id: string;
  text: string;
}) {
  const ref = useContext(SearchRefContext);
  return (
    <Button
      id={id}
      onClick={() => {
        ref?.current?.focus();
      }}
      className="flex cursor-pointer flex-row items-center gap-2 rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-500 hover:border-zinc-800 hover:text-zinc-800 focus:border-zinc-800 focus:text-zinc-800 focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
    >
      <IconSearch className="size-4" />
      <span>{text}</span>
    </Button>
  );
}
