"use client";

import StatsTable, {
  EntityStatsTableColumn,
} from "@/app/_components/statsTable";
import { EntityStatsType } from "@/app/ceremony/[iteration]/types";
import { Input } from "@headlessui/react";
import { IconListSearch } from "@tabler/icons-react";
import { useState } from "react";

export default function CategoryStats({
  entityStats,
}: {
  entityStats: EntityStatsType[];
}) {
  const COLS: EntityStatsTableColumn[] = [
    {
      name: "NAME",
      fullName: "Name",
      align: "left",
      default: "asc",
      sortKey: "aliases",
      minor: false,
    },
    {
      name: "CAT.NOMS",
      fullName: "Category Nominations",
      align: "center",
      default: "desc",
      sortKey: "career_category_noms",
      minor: false,
    },
    {
      name: "CAT.WINS",
      fullName: "Category Wins",
      align: "center",
      default: "desc",
      sortKey: "career_category_wins",
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
  const [search, setSearch] = useState("");
  return (
    <div>
      <div className="flex h-14 flex-row items-end pb-1">
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
      <StatsTable
        stats={entityStats}
        cols={COLS}
        searchKey="aliases"
        search={search}
        open={true}
      />
    </div>
  );
}
