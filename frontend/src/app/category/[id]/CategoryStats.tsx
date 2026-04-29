"use client";

import SearchField from "@/app/_components/SearchField";
import StatsTable, {
  EntityStatsTableColumn,
} from "@/app/_components/StatsTable";
import { EntityStatsType } from "@/app/ceremony/[iteration]/types";
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
      <div className="-mb-2 flex h-16 flex-row gap-6">
        <div className="mt-4 flex-1">
          <SearchField
            placeholder="Search names"
            onChange={(v) => setSearch(v)}
            className="z-10"
          />
        </div>
        <div className="hidden sm:flex sm:flex-1" />
      </div>
      <StatsTable
        stats={entityStats}
        cols={COLS}
        searchKey="aliases"
        search={search}
      />
    </div>
  );
}
