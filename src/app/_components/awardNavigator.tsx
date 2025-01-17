"use client";

import {
  SmallSelector,
  SmallSelectorOption,
} from "@/app/_components/selectors";
import { useState } from "react";
import { AwardType } from "../ceremony/[iteration]/types";
import { IconArrowRight } from "@tabler/icons-react";
import Link from "next/link";

export default function AwardNavigator({
  subdir,
  originalAwardType,
  options,
  originalOption,
}: {
  subdir: string;
  originalAwardType: AwardType;
  options: SmallSelectorOption[];
  originalOption: SmallSelectorOption;
}) {
  const awardOptions: SmallSelectorOption[] = [
    { id: AwardType.oscar, name: "Oscars" },
    { id: AwardType.emmy, name: "Emmys" },
  ];
  const originalAward = awardOptions[originalAwardType];
  const [award, setAward] = useState(originalAward);
  const [option, setOption] = useState(originalOption);
  const go = award.id !== originalAward.id || option.id !== originalOption.id;
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
        <SmallSelector state={option} setState={setOption} options={options} />
      </div>
      <Link
        href={`/${subdir}/${option.id}`}
        className={`${go ? "visible opacity-100" : "invisible opacity-0"} group absolute -right-1 -top-0.5 cursor-pointer p-1 transition-all duration-300 ease-in-out`}
      >
        <IconArrowRight className="size-4 stroke-zinc-500 group-hover:stroke-gold" />
      </Link>
    </div>
  );
}
