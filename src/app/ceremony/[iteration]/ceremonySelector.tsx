"use client";

import {
  SmallSelector,
  SmallSelectorOption,
} from "@/app/_components/selectors";
import { useState } from "react";
import { AwardType, EditionType } from "./types";
import { iterationToOrdinal } from "@/app/_utils/utils";
import { IconArrowRight } from "@tabler/icons-react";
import Link from "next/link";

export default function CeremonySelector({
  awardType,
  editions,
  currentId,
}: {
  awardType: AwardType;
  editions: EditionType[];
  currentId: number;
}) {
  const awardOptions: SmallSelectorOption[] = [
    { id: AwardType.oscar, name: "Oscars" },
    { id: AwardType.emmy, name: "Emmys" },
  ];
  const editionOptions: SmallSelectorOption[] = editions.map((e) => ({
    id: e.iteration,
    name: e.official_year + " (" + iterationToOrdinal(e.iteration) + ")",
  }));
  const originalAward = awardOptions[awardType];
  const originalEdition =
    editionOptions[editions.findIndex((e) => e.id === currentId)];
  const [award, setAward] = useState(originalAward);
  const [edition, setEdition] = useState(originalEdition);
  const go = award.id !== originalAward.id || edition.id !== originalEdition.id;
  return (
    <div className="relative">
      <div
        className={`${go ? "-translate-x-6" : ""} flex flex-row gap-2.5 transition-all duration-300 ease-in-out`}
      >
        <SmallSelector
          state={award}
          setState={setAward}
          options={awardOptions}
        />
        <SmallSelector
          state={edition}
          setState={setEdition}
          options={editionOptions}
        />
      </div>
      <Link
        href={`/ceremony/${edition.id}`}
        className={`${go ? "visible opacity-100" : "invisible opacity-0"} group absolute -right-1 -top-1 cursor-pointer p-1 transition-all duration-300 ease-in-out`}
      >
        <IconArrowRight className="size-4 stroke-zinc-500 group-hover:stroke-gold" />
      </Link>
    </div>
  );
}
