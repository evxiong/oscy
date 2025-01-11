"use client";

import {
  IconCaretDownFilled,
  IconCaretUpFilled,
  IconListSearch,
} from "@tabler/icons-react";
import { LargeSelector } from "@/app/_components/selectors";
import { Input } from "@headlessui/react";
import {
  EntityStatsType,
  AllStatsType,
  TitleStatsType,
  StatsType,
} from "./types";
import Link from "next/link";
import { useState, useEffect } from "react";

export default function Stats({ stats }: { stats: AllStatsType }) {
  const options = ["Films", "People"];
  const [selected, setSelected] = useState(options[0]);
  const [search, setSearch] = useState("");
  return (
    <div>
      <div className="flex h-14 flex-row items-end pb-1">
        <div className="flex-1">
          <LargeSelector
            state={selected}
            setState={setSelected}
            options={options}
          />
        </div>
        <div className="flex-1">
          <div className="flex h-8 flex-row items-center rounded-md border border-zinc-300 has-[input:focus-within]:outline has-[input:focus-within]:outline-2 has-[input:focus-within]:-outline-offset-2 has-[input:focus-within]:outline-zinc-400">
            <IconListSearch className="mx-2 h-4 w-4 stroke-zinc-400" />
            <Input
              name="Stats search"
              type="text"
              placeholder="Search"
              className="h-8 w-full bg-transparent pr-2 text-sm text-zinc-800 outline-none placeholder:text-zinc-400"
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>
      {selected === options[0] ? (
        <StatsTable
          key={0}
          stats={stats.title_stats}
          cols={TITLE_COLS}
          searchKey="title"
          search={search}
          open={selected === options[0]}
        />
      ) : (
        <StatsTable
          key={1}
          stats={stats.entity_stats}
          cols={ENTITY_COLS}
          searchKey="name"
          search={search}
          open={selected === options[0]}
        />
      )}
    </div>
  );
}

interface StatsTableColumn {
  name: string;
  fullName: string;
  align: "left" | "center";
  default: "asc" | "desc";
}

interface EntityStatsTableColumn extends StatsTableColumn {
  minor: boolean;
  sortKey: keyof EntityStatsType;
}

interface TitleStatsTableColumn extends StatsTableColumn {
  sortKey: keyof TitleStatsType;
}

const ENTITY_COLS: EntityStatsTableColumn[] = [
  {
    name: "NAME",
    fullName: "Name",
    align: "left",
    default: "asc",
    sortKey: "name",
    minor: false,
  },
  {
    name: "NOMS",
    fullName: "Nominations",
    align: "center",
    default: "desc",
    sortKey: "total_noms",
    minor: false,
  },
  {
    name: "WINS",
    fullName: "Wins",
    align: "center",
    default: "desc",
    sortKey: "total_wins",
    minor: false,
  },
  {
    name: "C.NOMS",
    fullName: "Career Nominations",
    align: "center",
    default: "desc",
    sortKey: "career_total_noms",
    minor: true,
  },
  {
    name: "C.WINS",
    fullName: "Career Wins",
    align: "center",
    default: "desc",
    sortKey: "career_total_wins",
    minor: true,
  },
];

const TITLE_COLS: TitleStatsTableColumn[] = [
  {
    name: "NAME",
    fullName: "Name",
    align: "left",
    default: "asc",
    sortKey: "title",
  },
  {
    name: "NOMS",
    fullName: "Nominations",
    align: "center",
    default: "desc",
    sortKey: "noms",
  },
  {
    name: "WINS",
    fullName: "Wins",
    align: "center",
    default: "desc",
    sortKey: "wins",
  },
];

function StatsTable<
  T1 extends StatsType,
  T2 extends StatsTableColumn,
  T3 extends keyof T1,
>({
  stats,
  cols,
  searchKey,
  search,
  open,
}: {
  stats: T1[];
  cols: T2[];
  searchKey: T3;
  search: string;
  open: boolean;
}) {
  // remove elements with duplicate ids
  const seen = new Set();
  const dedupedStats = stats.filter((e) => {
    const dup = seen.has(e.id);
    seen.add(e.id);
    return !dup;
  });

  const [desc, setDesc] = useState(true);
  const [selectedColInd, setSelectedColInd] = useState(1);
  const [sortedRows, setSortedRows] = useState<T1[]>(dedupedStats);

  useEffect(() => {
    setSortedRows(sortRows(dedupedStats, selectedColInd, desc, search));
  }, [search, open]);

  function setSortParams(ind: number) {
    let newDesc = ind !== selectedColInd ? cols[ind].default === "desc" : !desc;
    setDesc(newDesc);
    setSelectedColInd(ind);
    setSortedRows(sortRows(dedupedStats, ind, newDesc, search));
  }

  function filterRows(rows: T1[], search: string) {
    const query = search.toLowerCase().trim();
    return rows.filter((row) =>
      (row[searchKey] as string).toLowerCase().includes(query),
    );
  }

  function sortRows(rows: T1[], colInd: number, desc: boolean, search: string) {
    return filterRows(
      [...rows].sort((a, b) => {
        if (desc) {
          return (
            // @ts-ignore
            b[cols[colInd].sortKey]
              .toString()
              // @ts-ignore
              .localeCompare(a[cols[colInd].sortKey].toString(), "en", {
                numeric: true,
              })
          );
        } else {
          return (
            // @ts-ignore
            a[cols[colInd].sortKey]
              .toString()
              // @ts-ignore
              .localeCompare(b[cols[colInd].sortKey].toString(), "en", {
                numeric: true,
              })
          );
        }
      }),
      search,
    );
  }

  return (
    <table className="w-full border-collapse">
      <thead className="sticky top-0 h-10 select-none bg-white align-middle text-xxs font-semibold text-zinc-800">
        <tr className="h-10 border-b-2 border-zinc-300">
          <th scope="col" className="w-8 pt-1 text-zinc-500" title="Rank">
            #
          </th>
          {cols.map((c, i) => (
            <TableHeader
              key={i}
              align={c.align}
              name={c.name}
              fullName={c.fullName}
              selected={selectedColInd === i}
              desc={desc}
              colInd={i}
              setParams={setSortParams}
            />
          ))}
        </tr>
      </thead>
      <tbody className="w-full">
        {sortedRows.length > 0 ? (
          sortedRows.map((s, i) => (
            <TableRow
              key={i}
              row={i + 1}
              stat={s}
              cols={cols}
              searchKey={searchKey}
            />
          ))
        ) : (
          <tr>
            <td colSpan={cols.length + 1}>
              <div className="flex h-20 w-full select-none items-center justify-center text-xl text-zinc-500">
                <div>No results found</div>
              </div>
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}

function TableHeader({
  align,
  name,
  fullName,
  selected,
  desc,
  colInd,
  setParams,
}: {
  align: "left" | "center";
  name: string;
  fullName: string;
  selected: boolean;
  desc: boolean;
  colInd: number;
  setParams: (a: number) => void;
}) {
  return (
    <th
      scope="col"
      className={`${align === "left" ? "pl-3" : "w-9 px-2"} pt-1`}
    >
      <div
        className={`${align === "left" ? "justify-start" : "justify-center"} flex cursor-pointer items-center hover:opacity-75`}
        title={fullName}
        onClick={() => setParams(colInd)}
      >
        <div
          className={`${selected ? "underline" : ""} flex flex-row items-center gap-0.5 decoration-gold underline-offset-2`}
        >
          <div className="flex items-center justify-center">{name}</div>
          {selected &&
            (desc ? (
              <IconCaretDownFilled className="h-3 w-3 fill-gold" />
            ) : (
              <IconCaretUpFilled className="h-3 w-3 fill-gold" />
            ))}
        </div>
      </div>
    </th>
  );
}

function TableRow<
  T1 extends StatsType,
  T2 extends StatsTableColumn,
  T3 extends keyof T1,
>({
  row,
  stat,
  cols,
  searchKey,
}: {
  row: number;
  stat: T1;
  cols: T2[];
  searchKey: T3;
}) {
  return (
    <tr className="h-fit border-b border-zinc-200 text-base leading-5">
      <th
        scope="row"
        className="select-none text-xs font-semibold text-zinc-500"
      >
        {row}
      </th>
      {cols.map((c, i) => (
        <td
          key={i}
          className={`${c.align === "left" ? "py-3 pl-3" : "px-3 text-center font-medium"} ${"minor" in c && c.minor ? "font-normal text-zinc-500" : ""}`}
        >
          {
            // @ts-ignore
            c.sortKey === searchKey ? (
              <Link
                href={`/${(searchKey as string) === "name" ? "entity" : "title"}/${stat.id}`}
                className={`${(searchKey as string) === "name" ? "" : "italic"} line-clamp-2 cursor-pointer font-medium text-zinc-800 underline decoration-zinc-200 underline-offset-2 hover:text-gold`}
              >
                {stat[searchKey] as string}
              </Link>
            ) : (
              // @ts-ignore
              stat[c.sortKey]
            )
          }
        </td>
      ))}
    </tr>
  );
}
