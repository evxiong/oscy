"use client";

import {
  EntityStatsType,
  StatsType,
  TitleStatsType,
} from "../ceremony/[iteration]/types";
import { useState, useEffect } from "react";
import Link from "next/link";
import { IconCaretDownFilled, IconCaretUpFilled } from "@tabler/icons-react";

interface StatsTableColumn {
  name: string;
  fullName: string;
  align: "left" | "center";
  default: "asc" | "desc";
}

export interface EntityStatsTableColumn extends StatsTableColumn {
  minor: boolean;
  sortKey: keyof EntityStatsType;
}

export interface TitleStatsTableColumn extends StatsTableColumn {
  sortKey: keyof TitleStatsType;
}

export default function StatsTable<
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
      row[searchKey]!.toString().toLowerCase().includes(query),
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
    <div className="xs:overflow-x-visible xs:h-auto h-[90vh] overflow-x-auto">
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
    </div>
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
                // @ts-ignore
                title={
                  Array.isArray(stat[searchKey])
                    ? (stat[searchKey] as string[]).join(", ")
                    : stat[searchKey]
                }
                href={`/${(searchKey as string) === "aliases" ? "entity" : "title"}/${stat.id}`}
                className={`${(searchKey as string) === "aliases" ? "" : "italic"} line-clamp-2 cursor-pointer font-medium text-zinc-800 underline decoration-zinc-200 underline-offset-2 hover:text-gold`}
              >
                {Array.isArray(stat[searchKey])
                  ? (stat[searchKey] as any[])[0]
                  : stat[searchKey]}
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
