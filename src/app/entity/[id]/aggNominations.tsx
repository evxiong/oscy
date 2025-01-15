"use client";

import { Nominee } from "@/app/_components/nominations";
import { MediumSelector } from "@/app/_components/selectors";
import { dateToString, iterationToOrdinal } from "@/app/_utils/utils";
import { CategoryType, CeremonyType } from "@/app/ceremony/[iteration]/types";
import { Input } from "@headlessui/react";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function AggregateNominations({
  editions,
  searchHeader,
  stickyHeader,
}: {
  editions: CeremonyType[];
  searchHeader: string;
  stickyHeader: string;
}) {
  const searchKeys: (keyof CategoryType)[] = [
    "category_group",
    "official_name",
    "common_name",
    "short_name",
  ];
  const winnerOptions = [{ name: "All" }, { name: "Wins" }];
  const [winnerOption, setWinnerOption] = useState(winnerOptions[0]);
  const [search, setSearch] = useState("");
  const [filteredEditions, setFilteredEditions] =
    useState<CeremonyType[]>(editions);

  useEffect(() => {
    setFilteredEditions(
      filterEditions(
        editions,
        search,
        winnerOption.name === winnerOptions[1].name,
      ),
    );
  }, [search, winnerOption]);

  function filterEditions(
    editions: CeremonyType[],
    search: string,
    winnersOnly: boolean,
  ) {
    const query = search.toLowerCase().trim();
    return editions.filter(
      (e) =>
        (
          e.official_year +
          " " +
          e.ceremony_date.slice(0, 4) +
          " " +
          e.iteration.toString()
        ).includes(query) ||
        e.categories.some(
          (c) =>
            searchKeys.some(
              (k) =>
                c[k] !== "Other" &&
                (c[k] as string).toLowerCase().includes(query),
            ) &&
            (!winnersOnly || c.nominees.some((n) => n.winner)),
        ),
    );
  }

  return (
    <>
      <div className="sticky top-0 z-30 flex h-14 flex-row items-center justify-between gap-4 bg-white text-sm font-medium text-zinc-500">
        <div className="flex w-full flex-row items-center gap-4">
          <MediumSelector
            state={winnerOption}
            setState={setWinnerOption}
            options={winnerOptions}
            idKey="name"
            displayKey="name"
          />
          <div className="flex h-8 w-full flex-row-reverse items-center gap-0.5 rounded-md">
            <Input
              name="Category search"
              type="text"
              placeholder="All"
              className="peer h-8 w-full rounded-md bg-transparent px-1 text-sm text-zinc-800 outline-none placeholder:text-zinc-500"
              onChange={(e) => setSearch(e.target.value)}
            />
            <span className="select-none peer-focus:text-zinc-800">
              {searchHeader}:
            </span>
          </div>
        </div>
        <div className="flex-shrink-0 font-semibold">{stickyHeader}</div>
      </div>
      <hr />
      {filteredEditions.map(
        (e, i) =>
          (winnerOption.name === winnerOptions[0].name ||
            e.categories.some((c) => c.nominees.some((n) => n.winner))) && (
            <Edition
              key={i}
              editionInfo={e}
              search={search}
              searchKeys={searchKeys}
              winnersOnly={winnerOption.name === winnerOptions[1].name}
            />
          ),
      )}
    </>
  );
}

function Edition({
  editionInfo,
  search,
  searchKeys,
  winnersOnly,
}: {
  editionInfo: CeremonyType;
  search: string;
  searchKeys: (keyof CategoryType)[];
  winnersOnly: boolean;
}) {
  const query = search.toLowerCase().trim();
  return (
    <>
      <div className="flex flex-col gap-1 py-6 text-zinc-800 sm:flex-row sm:gap-6">
        <div className="sticky top-14 z-10 w-full flex-1 bg-white pb-4">
          <div className="sticky top-14 z-10">
            <Link
              href={`/ceremony/${editionInfo.iteration}`}
              className="w-fit cursor-pointer text-xl font-medium leading-6 hover:text-gold sm:text-lg sm:leading-6"
            >
              {iterationToOrdinal(editionInfo.iteration) + " Academy Awards"}
            </Link>
            <div className="mt-1 text-sm font-medium leading-4 text-zinc-500">
              {dateToString(editionInfo.ceremony_date)}
              <span className="select-none">
                &thinsp;&thinsp;·&thinsp;&thinsp;
              </span>
              {editionInfo.edition_noms}{" "}
              {editionInfo.edition_noms !== 1 ? "noms" : "nom"}
              <span className="select-none">
                &thinsp;&thinsp;·&thinsp;&thinsp;
              </span>
              {editionInfo.edition_wins}{" "}
              {editionInfo.edition_wins !== 1 ? "wins" : "win"}
            </div>
          </div>
        </div>
        <div className="mt-1 flex flex-1 flex-col gap-6">
          {editionInfo.categories.map(
            (c, i) =>
              (/\d/.test(search) ||
                searchKeys.some(
                  (k) =>
                    c[k] !== "Other" &&
                    (c[k] as string).toLowerCase().includes(query),
                )) &&
              (!winnersOnly || c.nominees.some((n) => n.winner)) && (
                <div key={i} className="flex flex-col gap-2">
                  <Link
                    href={`/category/${c.category_id}`}
                    className="w-fit max-w-full cursor-pointer truncate text-xs font-semibold text-zinc-800 hover:text-gold sm:text-xxs"
                  >
                    {c.common_name.toUpperCase()}
                  </Link>
                  <div className="flex flex-1 flex-col gap-[0.875rem]">
                    {c.nominees.map(
                      (n, j) =>
                        (!winnersOnly || (winnersOnly && n.winner)) && (
                          <Nominee
                            key={j}
                            category={c.short_name}
                            nomineeInfo={n}
                          />
                        ),
                    )}
                  </div>
                </div>
              ),
          )}
        </div>
      </div>
      <hr />
    </>
  );
}
