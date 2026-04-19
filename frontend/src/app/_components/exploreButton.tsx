"use client";

import { IconSearch } from "@tabler/icons-react";
import { useContext } from "react";
import { SearchRefContext } from "../_contexts/SearchRefContext";
import Button from "../_ui/Button";

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
    >
      <IconSearch className="size-4" />
      <span>{text}</span>
    </Button>
  );
}
