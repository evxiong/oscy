"use client";

import { Input } from "@headlessui/react";
import { IconArrowRight, IconSearch } from "@tabler/icons-react";
import Link from "next/link";
import {
  DependencyList,
  EffectCallback,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  CategoryResult,
  CeremonyResult,
  EntityResult,
  Result,
  SearchResults,
  TitleResult,
} from "../_types/types";
import { iterationToOrdinal } from "../_utils/utils";

export default function SearchBar() {
  const searchRef = useRef(null);
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
    if (searchRef.current && !e.composedPath().includes(searchRef.current)) {
      setOpenResults(false);
    }
  }

  function handleFocus(e: FocusEvent) {
    if (searchRef.current && !e.composedPath().includes(searchRef.current)) {
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
    const data = await fetch(`http://localhost:8000/search?query=${search}`);
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
    <div className="w-full max-w-[720px] sm:relative" ref={searchRef}>
      <div className="peer flex h-9 flex-row items-center rounded-md bg-zinc-100 has-[input:focus-within]:outline has-[input:focus-within]:outline-2 has-[input:focus-within]:-outline-offset-2 has-[input:focus-within]:outline-gold">
        <IconSearch className="mx-2 h-4 w-4 stroke-zinc-400" />
        <Input
          name="Search"
          type="text"
          placeholder="Search for people, titles, categories, or ceremonies"
          className="h-9 w-full bg-transparent pr-2 text-sm text-zinc-800 outline-none"
          onFocus={() => setOpenResults(true)}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <ResultsBox
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
  const callback = useCallback(effect, deps);
  useEffect(() => {
    const timeout = setTimeout(callback, delay);
    return () => clearTimeout(timeout);
  }, [callback, delay]);
}

function ResultsBox({
  open,
  blankSearch,
  results,
  closeResults,
}: {
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
          <QuickLinks closeResults={closeResults} />
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

function QuickLinks({ closeResults }: { closeResults: () => void }) {
  const pages = [
    {
      url: "/ceremony/96",
      name: "2023 (96th) Academy Awards",
      type: "ceremony",
    },
    { url: "/category/1", name: "Best Actor", type: "category" },
    { url: "/category/3", name: "Best Actress", type: "category" },
  ];
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xxs font-semibold text-zinc-500">QUICK LINKS</div>
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
