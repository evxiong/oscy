"use client";

import { IconListSearch } from "@tabler/icons-react";
import { LargeSelector } from "@/app/_components/selectors";
import { Input } from "@headlessui/react";
import { AllStatsType } from "./types";
import { useState } from "react";
import StatsTable, {
  EntityStatsTableColumn,
  TitleStatsTableColumn,
} from "@/app/_components/statsTable";

export default function CeremonyStats({ stats }: { stats: AllStatsType }) {
  const options = ["Films", "People"];
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
        />
      ) : (
        <StatsTable
          key={1}
          stats={stats.entity_stats}
          cols={ENTITY_COLS}
          searchKey="aliases"
          search={search}
        />
      )}
    </div>
  );
}
