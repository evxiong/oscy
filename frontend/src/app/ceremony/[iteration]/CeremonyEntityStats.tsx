"use client";

import SearchField from "@/app/_components/SearchField";
import type { EntityStatsTableColumn } from "@/app/_components/StatsTable";
import StatsTable from "@/app/_components/StatsTable";
import { useState } from "react";
import type { AllStatsType } from "./types";

export default function CeremonyEntityStats({
  stats,
}: {
  stats: AllStatsType;
}) {
  const ENTITY_COLS: EntityStatsTableColumn[] = [
    {
      name: "NAME",
      fullName: "Name",
      align: "left",
      default: "asc",
      sortKey: "aliases",
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
        stats={stats.entity_stats}
        cols={ENTITY_COLS}
        searchKey="aliases"
        search={search}
      />
    </div>
  );
}
