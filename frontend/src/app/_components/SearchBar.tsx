"use client";

import {
  IconArrowRight,
  IconLoader,
  IconSearch,
  IconX,
} from "@tabler/icons-react";
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
import merge from "../_utils/merge";
import { iterationToOrdinal } from "../_utils/utils";
import PrefetchLink from "./PrefetchLink";

export interface QuickLink {
  name: string;
  url: string;
  type: string;
}

export interface SearchResults {
  titles: SearchGroup;
  entities: SearchGroup;
  categories: SearchGroup;
  ceremonies: SearchGroup;
}

export interface Result {
  id: number;
  name: string;
  subdir: string;
  type: string;
  word_dist: number;
  dist: number;
}

export interface SearchGroup {
  page: number;
  next_page: number | null;
  page_size: number;
  length: number;
  results: EntityResult[] | TitleResult[] | CategoryResult[] | CeremonyResult[];
}

export interface EntityResult {
  id: number;
  imdb_id: string;
  type: string;
  name: string;
  aliases: string[];
  occurrences: number;
  iterations: number[];
  noms: number;
  wins: number;
  word_dist: number;
  dist: number;
}

export interface TitleResult {
  id: number;
  imdb_id: string;
  type: string;
  title: string;
  iterations: number[];
  noms: number;
  wins: number;
  word_dist: number;
  dist: number;
}

export interface CategoryResult {
  id: number;
  category: string;
  category_group_id: number;
  category_group: string;
  word_dist: number;
  dist: number;
}

export interface CeremonyResult {
  id: number;
  iteration: number;
  official_year: string;
  ceremony_date: string;
  word_dist: number;
  dist: number;
}

export default function SearchBar({ quickLinks }: { quickLinks: QuickLink[] }) {
  const searchRef = useRef(null);
  const inputRef = useContext(SearchRefContext);
  const [openResults, setOpenResults] = useState(false);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Result[]>();
  const [loading, setLoading] = useState(false);

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
      return;
    }

    setLoading(true);
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
    setLoading(false);
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
        onChange={(v) => {
          if (v.trim() === "") {
            setResults(undefined);
          }
          setSearch(v.trim());
        }}
      >
        <AriaGroup
          className={merge(
            "flex h-9 items-center overflow-hidden rounded-md bg-overlay px-2",
            "data-[focus-within]:outline data-[focus-within]:outline-2 data-[focus-within]:-outline-offset-2 data-[focus-within]:outline-gold",
          )}
        >
          <IconSearch aria-hidden className="size-4 shrink-0 stroke-tertiary" />
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
        quickLinks={quickLinks}
        open={openResults}
        loading={loading}
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
  quickLinks,
  open,
  loading,
  results,
  closeResults,
}: {
  quickLinks: QuickLink[];
  open: boolean;
  loading: boolean;
  results: Result[] | undefined;
  closeResults: () => void;
}) {
  return (
    <div
      className={`${open ? "visible opacity-100" : "invisible opacity-0"} absolute left-6 right-6 z-50 mt-2 rounded-md border border-border bg-background p-4 shadow-sm transition-all sm:left-0 sm:w-full`}
    >
      <div className="flex flex-col gap-4">
        {results === undefined ? (
          <QuickLinks
            quickLinks={quickLinks}
            loading={loading}
            closeResults={closeResults}
          />
        ) : (
          <Results
            results={results}
            loading={loading}
            closeResults={closeResults}
          />
        )}
      </div>
    </div>
  );
}

function Results({
  results,
  loading,
  closeResults,
}: {
  results: Result[];
  loading: boolean;
  closeResults: () => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between text-xxs/4 font-semibold text-secondary">
        <div className="uppercase">Results</div>
        {loading && <IconLoader className="size-4 animate-spin" />}
      </div>
      <div className="flex flex-col text-base/5 font-medium">
        {results.length === 0 ? (
          <div className="flex w-full items-center justify-center py-2.5 font-medium text-secondary">
            No results found.
          </div>
        ) : (
          results.map((r, i) => (
            <PrefetchLink
              key={i}
              href={`/${r.subdir}/${r.id}`}
              className="group -mx-1 flex cursor-pointer flex-col justify-start gap-0.5 rounded-md px-1 py-1.5 text-secondary hover:bg-hover hover:text-primary focus:bg-hover focus:text-primary"
              onClick={() => closeResults()}
            >
              <div className="flex flex-row items-center gap-2">
                <IconArrowRight aria-hidden className="size-3.5 shrink-0" />
                <div
                  className={`${r.type === "title" ? "italic" : ""} truncate pr-1 text-subtitle group-hover:text-primary group-focus:text-primary`}
                >
                  {r.name}
                </div>
              </div>
              <div className="ml-[22px] text-xxs font-semibold uppercase text-secondary">
                {r.type}
              </div>
            </PrefetchLink>
          ))
        )}
      </div>
    </div>
  );
}

function QuickLinks({
  quickLinks,
  loading,
  closeResults,
}: {
  quickLinks: QuickLink[];
  loading: boolean;
  closeResults: () => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between text-xxs/4 font-semibold text-secondary">
        <div className="uppercase">Quick Links</div>
        {loading && <IconLoader className="size-4 animate-spin" />}
      </div>
      <div className="flex flex-col text-sm font-medium">
        {quickLinks.map((quickLink, i) => (
          <Link
            key={i}
            href={quickLink.url}
            className="group -mx-1 flex cursor-pointer flex-row items-center justify-between gap-2 rounded-md px-1 py-1 pr-2 text-secondary hover:bg-hover hover:text-primary focus:bg-hover focus:text-primary"
            onClick={() => closeResults()}
          >
            <div className="flex flex-row items-center gap-2">
              <IconArrowRight aria-hidden className="size-3 shrink-0" />
              <div
                className={`${quickLink.type === "title" ? "italic" : ""} line-clamp-1 text-subtitle group-hover:text-primary group-focus:text-primary`}
              >
                {quickLink.name}
              </div>
            </div>
            <div className="text-xxs font-semibold uppercase text-secondary">
              {quickLink.type}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
