"use client";

import { IconStarFilled } from "@tabler/icons-react";
import { CategoryType, NomineeType } from "../ceremony/[iteration]/types";
import Link from "next/link";
import { useEffect, useState } from "react";
import { MediumSelector } from "@/app/_components/selectors";
import { Input } from "@headlessui/react";

export default function Nominations({
  categories,
  officialYear,
  ordinal,
}: {
  categories: CategoryType[];
  officialYear: string;
  ordinal: string;
}) {
  const searchKeys: (keyof CategoryType)[] = [
    "category_group",
    "official_name",
    "common_name",
    "short_name",
  ];
  const winnerOptions = ["All", "Winners"];
  const [winnersOnly, setWinnersOnly] = useState(winnerOptions[0]);
  const [search, setSearch] = useState("");
  const [filteredCategories, setFilteredCategories] =
    useState<CategoryType[]>(categories);

  useEffect(() => {
    setFilteredCategories(filterCategories(categories, search));
  }, [search]);

  function filterCategories(categories: CategoryType[], search: string) {
    const query = search.toLowerCase().trim();
    return categories.filter((c) =>
      searchKeys.some((k) => (c[k] as string).toLowerCase().includes(query)),
    );
  }

  return (
    <>
      <div className="sticky top-0 z-30 flex h-14 flex-row items-center justify-between gap-4 bg-white text-sm font-medium text-zinc-500">
        <div className="flex w-full flex-row items-center gap-4">
          <MediumSelector
            state={winnersOnly}
            setState={setWinnersOnly}
            options={winnerOptions}
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
              Category:
            </span>
          </div>
        </div>
        <div className="flex-shrink-0 font-semibold">
          {officialYear} ({ordinal})
        </div>
      </div>
      <hr />
      {filteredCategories.map((c, i) => (
        <Category
          key={i}
          categoryInfo={c}
          winnersOnly={winnersOnly === winnerOptions[1]}
        />
      ))}
    </>
  );
}

function Category({
  categoryInfo,
  winnersOnly,
}: {
  categoryInfo: CategoryType;
  winnersOnly: boolean;
}) {
  return (
    <>
      <div className="flex flex-col gap-1 py-6 text-zinc-800 sm:flex-row sm:gap-6">
        <div className="sticky top-14 z-20 flex-1 bg-white pb-4">
          <Link
            href={`/category/${categoryInfo.category_id}`}
            className="sticky top-14 flex w-fit cursor-pointer text-xl font-medium leading-6 hover:text-gold sm:text-lg sm:leading-6"
          >
            {categoryInfo.common_name}
          </Link>
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

function Nominee({
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
        className={`${nomineeInfo.winner ? "visible" : "invisible"} mt-[3px] h-4 w-4 flex-shrink-0 fill-gold`}
      />
      <div
        className={`${personFirst ? "flex-col" : "flex-col-reverse"} flex gap-1`}
      >
        <div
          className={`${personFirst ? "text-base font-medium leading-5 text-zinc-800" : "text-sm font-normal leading-4 text-zinc-500"}`}
        >
          {nomineeInfo.people.map((p, i) => (
            <span key={i}>
              <Link
                href={`/entity/${p.id}`}
                className="w-fit cursor-pointer underline decoration-zinc-300 underline-offset-2 hover:text-gold"
              >
                {p.name}
              </Link>
              {i !== nomineeInfo.people.length - 1 && ", "}
            </span>
          ))}
          {personFirst && nomineeInfo.note && <Note text={nomineeInfo.note} />}
        </div>
        <div
          className={`${!personFirst ? "text-base font-medium leading-5 text-zinc-800" : "text-sm font-normal leading-4 text-zinc-500"}`}
        >
          {nomineeInfo.titles.map((t, i) => {
            return (
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
                  <Link
                    href={`/title/${t.id}`}
                    className="w-fit cursor-pointer italic underline decoration-zinc-300 underline-offset-2 hover:text-gold"
                  >
                    {t.title}
                  </Link>
                  {i !== nomineeInfo.titles.length - 1 && (
                    <span className="select-none">&nbsp;&thinsp;·&nbsp;</span>
                  )}
                </span>
              </span>
            );
          })}
          {!nomineeInfo.is_person &&
            nomineeInfo.titles.length !== 0 &&
            nomineeInfo.note && <Note text={nomineeInfo.note} />}
        </div>
      </div>
    </div>
  );
}

function Note({ text }: { text: string }) {
  return (
    <span className="select-none">
      &nbsp;
      <span
        className="group relative z-0 cursor-pointer align-top text-xs font-medium text-gold"
        title={text}
      >
        <span className="z-0 group-hover:underline">N</span>
      </span>
    </span>
  );
}
