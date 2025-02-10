"use client";

import { createContext, useRef } from "react";

export const SearchRefContext =
  createContext<React.RefObject<HTMLElement | null> | null>(null);

export default function SearchRefContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const ref: React.RefObject<HTMLElement | null> = useRef(null);
  return (
    <SearchRefContext.Provider value={ref}>
      {children}
    </SearchRefContext.Provider>
  );
}
