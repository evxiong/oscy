"use client";

import { MediumSelector } from "@/app/_components/selectors";
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
    <div className="flex flex-col gap-6 text-zinc-800 sm:flex-row sm:gap-6">
      <table className="w-full border-collapse">
        <thead className="text-xxs font-semibold text-zinc-800">
          <tr className="h-14 border-b border-zinc-300">
            <th scope="col">
              <div className="flex w-full flex-row items-center gap-4">
                <MediumSelector
                  state={option}
                  setState={setOption}
                  options={options}
                  idKey="name"
                  displayKey="name"
                />
                {option.name === options[1].name ? (
                  <MediumSelector
                    state={categoryOption}
                    setState={setCategoryOption}
                    options={categoryOptions}
                    idKey="category_id"
                    displayKey="category"
                  />
                ) : options.length > 2 && option.name === options[2].name ? (
                  <MediumSelector
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
            </th>
            <th
              scope="col"
              className="w-16 text-center align-middle sm:w-20 sm:pb-4 sm:align-bottom"
            >
              COUNT
            </th>
            <th
              scope="col"
              className="w-16 text-center align-middle sm:w-20 sm:pb-4 sm:align-bottom"
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
  );
}
