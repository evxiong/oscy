"use client";

import SearchField from "@/app/_components/SearchField";
import type { TitleStatsTableColumn } from "@/app/_components/StatsTable";
import StatsTable from "@/app/_components/StatsTable";
import { useState } from "react";
import type { AllStatsType } from "./types";

export default function CeremonyTitleStats({ stats }: { stats: AllStatsType }) {
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
  const [search, setSearch] = useState("");
  return (
    <div>
      <div className="-mb-2 flex h-16 flex-row gap-6">
        <div className="mt-4 flex-1">
          <SearchField
            placeholder="Search titles"
            onChange={(v) => setSearch(v)}
            className="z-10"
          />
        </div>
        <div className="hidden sm:flex sm:flex-1" />
      </div>
      <StatsTable
        stats={stats.title_stats}
        cols={TITLE_COLS}
        searchKey="title"
        search={search}
      />
    </div>
  );
}
