"use client";

import { IconArrowRight, IconSearch, IconX } from "@tabler/icons-react";
import Link from "next/link";
import {
  DependencyList,
  EffectCallback,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Button as AriaButton,
  Group as AriaGroup,
  Input as AriaInput,
  SearchField as AriaSearchField,
} from "react-aria-components";
import { SearchRefContext } from "../_contexts/SearchRefContext";
import {
  CategoryResult,
  CeremonyResult,
  EntityResult,
  Result,
  SearchResults,
  TitleResult,
} from "../_types/types";
import merge from "../_utils/merge";
import { iterationToOrdinal } from "../_utils/utils";

export default function SearchBar({
  currentEdition,
}: {
  currentEdition: number;
}) {
  const searchRef = useRef(null);
  const inputRef = useContext(SearchRefContext);
  const [openResults, setOpenResults] = useState(false);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Result[]>([]);

  // for closing search results box
  useEffect(() => {
    document.body.addEventListener("click", handleClick);
    document.body.addEventListener("focusin", handleFocus);
    return () => {
      document.body.removeEventListener("click", handleClick);
      document.body.removeEventListener("focusin", handleFocus);
    };
  }, []);

  function handleClick(e: MouseEvent) {
    if (
      searchRef.current &&
      !(e.target as HTMLElement).id.startsWith("explore") &&
      !e.composedPath().includes(searchRef.current)
    ) {
      setOpenResults(false);
    }
  }

  function handleFocus(e: FocusEvent) {
    if (
      searchRef.current &&
      !(e.target as HTMLElement).id.startsWith("explore") &&
      !e.composedPath().includes(searchRef.current)
    ) {
      setOpenResults(false);
    }
  }

  function closeResults() {
    setOpenResults(false);
  }

  async function fetchResults() {
    if (search.trim() === "") {
      setResults([]);
      return;
    }
    const data = await fetch(`/api/search?query=${search}`);
    const searchResults: SearchResults = await data.json();
    const r: Result[] = [];
    if (searchResults.titles) {
      for (const e of searchResults.titles.results as TitleResult[]) {
        r.push({
          id: e.id,
          name: e.title,
          subdir: "title",
          type: "title",
          word_dist: e.word_dist,
          dist: e.dist,
        });
      }
    }
    if (searchResults.entities) {
      for (const e of searchResults.entities.results as EntityResult[]) {
        r.push({
          id: e.id,
          name: e.name,
          subdir: "entity",
          type: e.type,
          word_dist: e.word_dist,
          dist: e.dist,
        });
      }
    }
    if (searchResults.categories) {
      for (const e of searchResults.categories.results as CategoryResult[]) {
        r.push({
          id: e.id,
          name: e.category,
          subdir: "category",
          type: "category",
          word_dist: e.word_dist,
          dist: e.dist,
        });
      }
    }
    if (searchResults.ceremonies) {
      for (const e of searchResults.ceremonies.results as CeremonyResult[]) {
        r.push({
          id: e.iteration,
          name:
            e.official_year +
            " (" +
            iterationToOrdinal(e.iteration) +
            ") Academy Awards",
          subdir: "ceremony",
          type: "ceremony",
          word_dist: e.word_dist,
          dist: e.dist,
        });
      }
    }
    r.sort((a, b) => a.word_dist - b.word_dist);
    setResults(r.slice(0, 10));
  }

  useDebounce(
    () => {
      fetchResults();
    },
    [search],
    250,
  );

  return (
    <div className="w-full min-w-0 max-w-[720px] sm:relative" ref={searchRef}>
      <AriaSearchField
        className="group/field w-full text-sm font-normal"
        onChange={(v) => setSearch(v)}
      >
        <AriaGroup
          className={merge(
            "flex h-9 items-center overflow-hidden rounded-md bg-overlay px-2",
            "data-[focus-within]:outline data-[focus-within]:outline-2 data-[focus-within]:-outline-offset-2 data-[focus-within]:outline-gold",
          )}
        >
          <IconSearch className="size-4 shrink-0 stroke-tertiary" />
          <AriaInput
            placeholder="Search for people, titles, categories, or ceremonies"
            className="min-w-0 flex-1 bg-overlay p-1.5 text-primary outline-none placeholder:text-tertiary [&::-webkit-search-cancel-button]:hidden"
            onFocus={() => setOpenResults(true)}
            ref={(v) => {
              if (inputRef) {
                inputRef.current = v;
              }
            }}
          />
          <AriaButton className="group/button -m-1.5 p-1.5 group-data-[empty]/field:hidden">
            <IconX className="size-4 stroke-tertiary group-hover/button:stroke-secondary" />
          </AriaButton>
        </AriaGroup>
      </AriaSearchField>

      <ResultsBox
        currentEdition={currentEdition}
        open={openResults}
        blankSearch={search.trim() === ""}
        results={results}
        closeResults={closeResults}
      />
    </div>
  );
}

/* https://stackoverflow.com/questions/69727243/react-search-using-debounce */
function useDebounce(
  effect: EffectCallback,
  deps: DependencyList,
  delay: number,
) {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const callback = useCallback(effect, deps);
  useEffect(() => {
    const timeout = setTimeout(callback, delay);
    return () => clearTimeout(timeout);
  }, [callback, delay]);
}

function ResultsBox({
  currentEdition,
  open,
  blankSearch,
  results,
  closeResults,
}: {
  currentEdition: number;
  open: boolean;
  blankSearch: boolean;
  results: Result[];
  closeResults: () => void;
}) {
  return (
    <div
      className={`${open ? "visible opacity-100" : "invisible opacity-0"} absolute left-6 right-6 z-50 mt-2 rounded-md border border-zinc-200 bg-white p-4 transition-all sm:left-0 sm:w-full`}
    >
      <div className="flex flex-col gap-4">
        {blankSearch ? (
          <QuickLinks
            currentEdition={currentEdition}
            closeResults={closeResults}
          />
        ) : (
          <Results results={results} closeResults={closeResults} />
        )}
      </div>
    </div>
  );
}

function Results({
  results,
  closeResults,
}: {
  results: Result[];
  closeResults: () => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xxs font-semibold text-zinc-500">RESULTS</div>
      <div className="flex flex-col text-base font-medium leading-5">
        {results.map((r, i) => (
          <Link
            prefetch={false}
            key={i}
            href={`/${r.subdir}/${r.id}`}
            className="group -mx-1 flex cursor-pointer flex-col justify-start gap-0.5 rounded-md px-1 py-1.5 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800 focus:bg-zinc-100 focus:text-zinc-800 focus:outline-none"
            onClick={() => closeResults()}
          >
            <div className="flex flex-row items-center gap-2">
              <IconArrowRight className="size-3.5 flex-shrink-0" />
              <div
                className={`${r.type === "title" ? "italic" : ""} truncate pr-1 text-zinc-600 group-hover:text-zinc-800 group-focus:text-zinc-800`}
              >
                {r.name}
              </div>
            </div>
            <div className="ml-[22px] text-xxs font-semibold text-zinc-400">
              {r.type.toUpperCase()}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function QuickLinks({
  currentEdition,
  closeResults,
}: {
  currentEdition: number;
  closeResults: () => void;
}) {
  const currentYear = 1927 + currentEdition;
  const currentOrdinal = iterationToOrdinal(currentEdition);
  const pages = [
    {
      url: `/ceremony/${currentEdition}`,
      name: `${currentYear} (${currentOrdinal}) Academy Awards`,
      type: "ceremony",
    },
    { url: "/category/46", name: "Best Picture", type: "category" },
    { url: "/category/1", name: "Best Actor", type: "category" },
    { url: "/category/3", name: "Best Actress", type: "category" },
  ];
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xxs font-semibold uppercase text-zinc-500">
        Quick Links
      </div>
      <div className="flex flex-col text-sm font-medium">
        {pages.map((p, i) => (
          <Link
            key={i}
            href={p.url}
            className="group -mx-1 flex cursor-pointer flex-row items-center justify-between gap-2 rounded-md px-1 py-1 pr-2 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800 focus:bg-zinc-100 focus:text-zinc-800 focus:outline-none"
            onClick={() => closeResults()}
          >
            <div className="flex flex-row items-center gap-2">
              <IconArrowRight className="size-3 flex-shrink-0" />
              <div
                className={`${p.type === "title" ? "italic" : ""} line-clamp-1 text-zinc-600 group-hover:text-zinc-800 group-focus:text-zinc-800`}
              >
                {p.name}
              </div>
            </div>
            <div className="text-xxs font-semibold text-zinc-400">
              {p.type.toUpperCase()}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
