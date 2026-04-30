"use client";

import { Nominee } from "@/app/_components/Nominations";
import SearchField from "@/app/_components/SearchField";
import Switch from "@/app/_ui/Switch";
import { dateToString, iterationToOrdinal } from "@/app/_utils/utils";
import { CategoryType, CeremonyType } from "@/app/ceremony/[iteration]/types";
import { useEffect, useMemo, useState } from "react";
import PrefetchLink from "./PrefetchLink";

export default function AggregateNominations({
  editions,
}: {
  editions: CeremonyType[];
}) {
  const searchKeys: (keyof CategoryType)[] = useMemo(
    () => ["category_group", "official_name", "common_name", "short_name"],
    [],
  );
  const [winnersOnly, setWinnersOnly] = useState(false);
  const [search, setSearch] = useState("");
  const [filteredEditions, setFilteredEditions] =
    useState<CeremonyType[]>(editions);

  useEffect(() => {
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

    setFilteredEditions(filterEditions(editions, search, winnersOnly));
  }, [editions, search, winnersOnly, searchKeys]);

  return (
    <>
      <div className="hide-scrollbar sticky top-0 z-30 -mx-0.5 flex h-[--nominations-header-height-mobile] flex-col justify-center gap-3 overflow-x-auto bg-background px-0.5 text-sm font-medium text-secondary sm:h-[--nominations-header-height] sm:flex-row sm:items-center sm:gap-6">
        <div className="sm:flex-1">
          <SearchField
            placeholder="Search editions or category names"
            onChange={(v) => setSearch(v)}
          />
        </div>
        <div className="flex sm:flex-1 sm:justify-end">
          <Switch isSelected={winnersOnly} onChange={setWinnersOnly}>
            Wins only
          </Switch>
        </div>
      </div>
      <hr />
      {filteredEditions.map(
        (e, i) =>
          (!winnersOnly ||
            e.categories.some((c) => c.nominees.some((n) => n.winner))) && (
            <Edition
              key={i}
              editionInfo={e}
              search={search}
              searchKeys={searchKeys}
              winnersOnly={winnersOnly}
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
      <div className="flex flex-col gap-1 py-6 text-primary sm:flex-row sm:gap-6">
        <div className="sticky top-[--nominations-header-height-mobile] z-10 w-full flex-1 bg-background pb-4 sm:top-[--nominations-header-height] sm:pb-0">
          <div className="sticky top-[--nominations-header-height-mobile] z-10 sm:top-[--nominations-header-height]">
            <PrefetchLink
              href={`/ceremony/${editionInfo.iteration}`}
              className="w-fit cursor-pointer text-xl/6 font-medium hover:text-gold sm:text-lg/6"
            >
              {iterationToOrdinal(editionInfo.iteration) + " Academy Awards"}
            </PrefetchLink>
            <div className="mt-1 text-sm/4 font-medium text-secondary">
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
                  <PrefetchLink
                    title={c.common_name}
                    href={`/category/${c.category_id}`}
                    className="cursor-pointer text-xs font-semibold text-primary hover:text-gold sm:text-xxs"
                  >
                    {c.common_name.toUpperCase()}
                  </PrefetchLink>
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
