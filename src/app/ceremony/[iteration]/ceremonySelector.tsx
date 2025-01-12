"use client";

import { SmallSelector } from "@/app/_components/selectors";
import { useState } from "react";
import { AwardType, EditionType } from "./types";
import { iterationToOrdinal } from "@/app/_utils/utils";
import { IconArrowRight } from "@tabler/icons-react";
import { Button } from "@headlessui/react";

export default function CeremonySelector({
  awardType,
  editions,
  currentId,
}: {
  awardType: AwardType;
  editions: EditionType[];
  currentId: number;
}) {
  const awardOptions = ["Oscars", "Emmys"];
  const editionOptions = editions.map(
    (e) => e.official_year + " (" + iterationToOrdinal(e.iteration) + ")",
  );
  const originalAward = awardOptions[awardType];
  const originalEdition =
    editionOptions[editions.findIndex((e) => e.id === currentId)];
  const [award, setAward] = useState(originalAward);
  const [edition, setEdition] = useState(originalEdition);
  const go = award !== originalAward || edition != originalEdition;
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
      <Button
        className={`${go ? "visible opacity-100" : "invisible opacity-0"} group absolute -right-1 -top-1 cursor-pointer p-1 transition-all duration-300 ease-in-out`}
      >
        <IconArrowRight className="size-4 stroke-zinc-500 group-hover:stroke-gold" />
      </Button>
    </div>
  );
}
