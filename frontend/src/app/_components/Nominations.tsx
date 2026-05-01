"use client";

import { IconStarFilled } from "@tabler/icons-react";
import { useEffect, useMemo, useState } from "react";
import {
  Button as AriaButton,
  DialogTrigger as AriaDialogTrigger,
  OverlayArrow as AriaOverlayArrow,
  Popover as AriaPopover,
} from "react-aria-components";
import Switch from "../_ui/Switch";
import { iterationToOrdinal } from "../_utils/utils";
import {
  CategoryType,
  CeremonyType,
  NomineeType,
} from "../ceremony/[iteration]/types";
import PrefetchLink from "./PrefetchLink";
import SearchField from "./SearchField";

export interface NominationCategoryType extends CategoryType {
  ceremony_id: number;
  year_and_ordinal: string;
}

export default function Nominations({
  showCeremony,
  editions,
  searchKeys,
}: {
  showCeremony: boolean;
  editions: CeremonyType[];
  searchKeys: (keyof NominationCategoryType)[];
}) {
  const categories: NominationCategoryType[] = useMemo(
    () =>
      editions
        .map((e) =>
          e.categories.map((c) => ({
            ...c,
            ceremony_id: e.iteration,
            year_and_ordinal:
              e.official_year + " (" + iterationToOrdinal(e.iteration) + ")",
          })),
        )
        .flat(),
    [editions],
  );
  const [winnersOnly, setWinnersOnly] = useState(false);
  const [search, setSearch] = useState("");
  const [filteredCategories, setFilteredCategories] =
    useState<NominationCategoryType[]>(categories);

  useEffect(() => {
    function filterCategories(
      categories: NominationCategoryType[],
      search: string,
    ) {
      const query = search.toLowerCase().trim();
      return categories.filter((c) =>
        searchKeys.some(
          (k) =>
            c[k] !== "Other" && (c[k] as string).toLowerCase().includes(query),
        ),
      );
    }

    setFilteredCategories(filterCategories(categories, search));
  }, [search, categories, searchKeys]);

  return (
    <>
      <div className="hide-scrollbar sticky top-0 z-30 -mx-0.5 flex h-[--nominations-header-height-mobile] flex-col justify-center gap-3 overflow-x-auto bg-background px-0.5 text-sm font-medium text-secondary sm:h-[--nominations-header-height] sm:flex-row sm:items-center sm:gap-6">
        <div className="sm:flex-1">
          <SearchField
            placeholder={
              showCeremony
                ? "Search editions or category names"
                : "Search categories"
            }
            onChange={(v) => setSearch(v)}
          />
        </div>
        <div className="flex sm:flex-1 sm:justify-end">
          <Switch isSelected={winnersOnly} onChange={setWinnersOnly}>
            Winners only
          </Switch>
        </div>
      </div>
      <hr />
      {filteredCategories.map((c, i) => (
        <Category
          key={i}
          showCeremony={showCeremony}
          categoryInfo={c}
          winnersOnly={winnersOnly}
        />
      ))}
    </>
  );
}

function Category({
  showCeremony,
  categoryInfo,
  winnersOnly,
}: {
  showCeremony: boolean;
  categoryInfo: NominationCategoryType;
  winnersOnly: boolean;
}) {
  return (
    <>
      <div className="flex flex-col gap-1 py-6 text-primary sm:flex-row sm:gap-6">
        <div className="sticky top-[--nominations-header-height-mobile] z-10 w-full flex-1 bg-background pb-4 sm:top-[--nominations-header-height] sm:pb-0">
          <div className="sticky top-[--nominations-header-height-mobile] z-10 sm:top-[--nominations-header-height]">
            <PrefetchLink
              href={
                showCeremony
                  ? `/ceremony/${categoryInfo.ceremony_id}`
                  : `/category/${categoryInfo.category_id}`
              }
              className="w-fit cursor-pointer text-xl/6 font-medium hover:text-gold sm:text-lg/6"
            >
              {showCeremony
                ? categoryInfo.year_and_ordinal
                : categoryInfo.common_name}
            </PrefetchLink>
            {showCeremony && (
              <div className="mt-1 text-sm/4 font-medium text-secondary">
                {categoryInfo.common_name}
              </div>
            )}
          </div>
        </div>
        <div className="flex flex-1 flex-col gap-[0.875rem]">
          {categoryInfo.nominees.map(
            (n, i) =>
              (!winnersOnly || (winnersOnly && n.winner)) && (
                <Nominee
                  key={i}
                  category={categoryInfo.short_name}
                  nomineeInfo={n}
                />
              ),
          )}
        </div>
      </div>
      <hr />
    </>
  );
}

export function Nominee({
  category,
  nomineeInfo,
}: {
  category: string;
  nomineeInfo: NomineeType;
}) {
  const personFirst = nomineeInfo.is_person || nomineeInfo.titles.length === 0;
  return (
    <div className="flex flex-row gap-2.5">
      <IconStarFilled
        aria-label="Winner"
        className={`${nomineeInfo.winner ? "visible" : "invisible"} mt-[3px] size-4 shrink-0 fill-gold`}
      />
      <div
        className={`${personFirst ? "flex-col" : "flex-col-reverse"} flex gap-1`}
      >
        {nomineeInfo.people.length > 0 && (
          <div
            className={`${personFirst ? "text-base/5 font-medium text-primary" : "text-sm/4 font-normal text-secondary"}`}
          >
            {nomineeInfo.people.map((p, i) => (
              <span key={i}>
                <PrefetchLink
                  href={`/entity/${p.id}`}
                  className="w-fit cursor-pointer underline decoration-underline underline-offset-2 hover:text-gold"
                >
                  {p.name}
                </PrefetchLink>
                {i !== nomineeInfo.people.length - 1 && ", "}
              </span>
            ))}
            {personFirst && nomineeInfo.note && (
              <Note text={nomineeInfo.note} />
            )}
          </div>
        )}
        {nomineeInfo.titles.length > 0 && (
          <div
            className={`${!personFirst ? "text-base/5 font-medium text-primary" : "text-sm/4 font-normal text-secondary"}`}
          >
            {nomineeInfo.titles.map((t, i) => (
              <span key={i}>
                {t.detail.map((d, j) => (
                  <span key={j}>
                    <span className="w-fit">
                      {category === "Original Song" ||
                      category === "Dance Direction"
                        ? "“" + d + "”"
                        : d}
                    </span>
                    {", "}
                  </span>
                ))}
                <span>
                  <PrefetchLink
                    href={`/title/${t.id}`}
                    className="w-fit cursor-pointer italic underline decoration-underline underline-offset-2 hover:text-gold"
                  >
                    {t.title}
                  </PrefetchLink>
                  {i !== nomineeInfo.titles.length - 1 && (
                    <span className="select-none">&nbsp;&thinsp;·&nbsp;</span>
                  )}
                </span>
              </span>
            ))}
            {!nomineeInfo.is_person &&
              nomineeInfo.titles.length !== 0 &&
              nomineeInfo.note && <Note text={nomineeInfo.note} />}
          </div>
        )}
      </div>
    </div>
  );
}

function Note({ text }: { text: string }) {
  let popoverText = text;
  if (popoverText.startsWith("[NOTE: ")) {
    popoverText = popoverText.slice(7);
  }
  if (popoverText.endsWith("]")) {
    popoverText = popoverText.slice(0, -1);
  }
  return (
    <span>
      &nbsp;
      <AriaDialogTrigger>
        <AriaButton
          aria-label="Note"
          className="align-top text-xxs font-semibold text-gold transition-colors hover:text-secondary focus-visible:text-secondary data-[pressed]:text-secondary"
        >
          <span title={text}>[N]</span>
        </AriaButton>
        <AriaPopover
          placement="top"
          className="max-w-96 rounded-md border border-border bg-background p-2.5 outline-none drop-shadow-md transition-opacity duration-300 data-[entering]:opacity-0"
        >
          <AriaOverlayArrow className="group/arrow">
            <svg
              width={12}
              height={12}
              viewBox="0 0 12 12"
              className="block fill-background stroke-border stroke-1 group-data-[placement='bottom']/arrow:rotate-180 group-data-[placement='left']/arrow:-rotate-90 group-data-[placement='right']/arrow:rotate-90"
            >
              <path d="M0 0 L6 6 L12 0" />
            </svg>
          </AriaOverlayArrow>
          <h2 className="text-xxs font-semibold uppercase text-title">Note</h2>
          <hr className="my-1.5 border-border" />
          <p className="mt-1 text-sm leading-[18px] text-subtitle">
            {popoverText}
          </p>
        </AriaPopover>
      </AriaDialogTrigger>
    </span>
  );
}
