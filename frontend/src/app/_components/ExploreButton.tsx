"use client";

import { IconSearch } from "@tabler/icons-react";
import { useContext } from "react";
import { SearchRefContext } from "../_contexts/SearchRefContext";
import Button from "../_ui/Button";

export default function ExploreButton({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  const ref = useContext(SearchRefContext);
  return (
    <Button
      id={id}
      variant="secondary"
      onClick={() => {
        ref?.current?.focus();
      }}
    >
      <IconSearch aria-hidden />
      {children}
    </Button>
  );
}
