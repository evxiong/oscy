"use client";

import { MediumSelectorAria } from "@/app/_components/selectors";
import { useState } from "react";
import {
  CategoryGroupRankings,
  CategoryRankings,
  OverallRankings,
} from "./types";

export default function Rankings({
  overallRankings,
  categoryRankings,
  categoryGroupRankings,
}: {
  overallRankings: OverallRankings;
  categoryRankings: CategoryRankings[];
  categoryGroupRankings: CategoryGroupRankings[];
}) {
  const options = [
    { name: "Overall" },
    { name: "Category" },
    { name: "Category Group" },
  ];
  const categoryOptions = categoryRankings;
  const categoryGroupOptions = categoryGroupRankings.filter(
    (r) => r.category_group !== "Other",
  );
  if (categoryGroupOptions.length === 0) {
    options.pop();
  }
  const [option, setOption] = useState(options[0]);
  const [categoryOption, setCategoryOption] = useState(categoryRankings[0]);
  const [categoryGroupOption, setCategoryGroupOption] = useState(
    categoryGroupOptions[0],
  );
  return (
    <>
      <div className="hide-scrollbar -mx-0.5 -mb-2 flex h-16 flex-row items-center gap-3 overflow-x-auto px-0.5">
        <MediumSelectorAria
          state={option}
          setState={setOption}
          options={options}
          idKey="name"
          displayKey="name"
        />
        {option.name === options[1].name ? (
          <MediumSelectorAria
            state={categoryOption}
            setState={setCategoryOption}
            options={categoryOptions}
            idKey="category_id"
            displayKey="category"
          />
        ) : options.length > 2 && option.name === options[2].name ? (
          <MediumSelectorAria
            state={categoryGroupOption}
            setState={setCategoryGroupOption}
            options={categoryGroupOptions}
            idKey="category_group_id"
            displayKey="category_group"
          />
        ) : (
          <></>
        )}
      </div>

      <div className="flex flex-col gap-6 text-zinc-800 sm:flex-row sm:gap-6">
        <table className="w-full border-collapse">
          <thead className="text-xxs text-zinc-800">
            <tr className="h-10 border-b border-border align-middle">
              <th scope="col" className="text-left font-semibold">
                STAT
              </th>
              <th
                scope="col"
                className="text-center font-semibold sm:w-20 sm:min-w-16"
              >
                COUNT
              </th>
              <th
                scope="col"
                className="text-center font-semibold sm:w-20 sm:min-w-16"
              >
                RANK
              </th>
            </tr>
          </thead>
          <tbody className="text-lg">
            <tr className="border-b border-zinc-200">
              <th className="py-6 text-left font-medium">Nominations</th>
              <td className="text-center text-xl font-medium">
                {option.name === options[0].name
                  ? overallRankings.overall_noms
                  : option.name === options[1].name
                    ? categoryOption.category_noms
                    : categoryGroupOption.category_group_noms}
              </td>
              <td className="text-center text-xl font-medium text-zinc-500">
                {option.name === options[0].name
                  ? overallRankings.overall_noms_rank
                  : option.name === options[1].name
                    ? categoryOption.category_noms_rank
                    : categoryGroupOption.category_group_noms_rank}
              </td>
            </tr>
            <tr className="border-b border-zinc-200">
              <th className="py-6 text-left font-medium">Wins</th>
              <td className="text-center text-xl font-medium">
                {option.name === options[0].name
                  ? overallRankings.overall_wins
                  : option.name === options[1].name
                    ? categoryOption.category_wins
                    : categoryGroupOption.category_group_wins}
              </td>
              <td className="text-center text-xl font-medium text-zinc-500">
                {option.name === options[0].name
                  ? overallRankings.overall_wins_rank
                  : option.name === options[1].name
                    ? categoryOption.category_wins_rank
                    : categoryGroupOption.category_group_wins_rank}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}
