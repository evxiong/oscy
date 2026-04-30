import AwardNavigator from "@/app/_components/AwardNavigator";
import Breadcrumbs from "@/app/_components/Breadcrumbs";
import type { SmallSelectorOption } from "@/app/_components/Selectors";
import { fetchApi, fetchVersion } from "@/app/_utils/fetch";
import { categoryNamesToTimeline } from "@/app/_utils/utils";
import { AwardEnum } from "@/app/ceremony/[iteration]/types";
import { notFound } from "next/navigation";
import type { CategoryGroupInfo, CategoryInfo } from "./types";

export default async function CategoryLayout({
  params,
  children,
}: {
  params: Promise<{ id: string }>;
  children: React.ReactNode;
}) {
  const categoryId = parseInt((await params).id);
  const categoryGroups: CategoryGroupInfo[] = await fetchApi("/categories");

  let category: CategoryInfo | undefined = undefined;
  let categoryGroup = "";
  for (const cg of categoryGroups) {
    for (const c of cg.categories) {
      if (c.category_id === categoryId) {
        category = c;
        categoryGroup = cg.category_group;
      }
    }
  }

  if (category === undefined) {
    notFound();
  }

  const awardNavigatorOptions: SmallSelectorOption[] = categoryGroups.flatMap(
    (cg) =>
      cg.categories.map((c) => ({
        id: c.category_id,
        name: c.category,
        disabled: false,
      })),
  );
  const originalAwardNavigatorOption: SmallSelectorOption =
    awardNavigatorOptions.find((e) => e.id === categoryId)!;

  const categoryName = category.category.startsWith("Unique")
    ? category.category
    : "Best " + category.category;
  const numCeremonies = category.category_names.reduce(
    (acc1, cn) =>
      acc1 + cn.ranges.reduce((acc2, r) => acc2 + r[1] - r[0] + 1, 0),
    0,
  );
  const timeline = categoryNamesToTimeline(category.category_names);
  const firstYear = timeline.at(-1)!.start_year;
  const lastYear = timeline[0].end_year;

  const currentEdition = (await fetchVersion()).iteration;

  return (
    <div className="flex flex-col gap-5">
      <nav className="mx-auto flex w-full flex-row justify-between px-6 pt-5 text-xs md:w-[768px]">
        <Breadcrumbs
          crumbs={[
            { name: "Home", link: "/" },
            { name: "Category", link: "" },
          ]}
        />
        <AwardNavigator
          subdir="category"
          originalAwardType={AwardEnum.oscar}
          options={awardNavigatorOptions}
          originalOption={originalAwardNavigatorOption}
        />
      </nav>
      <div className="mx-auto flex w-full flex-row items-center justify-between px-6 md:w-[768px]">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl/7 font-medium text-primary">
            {categoryName}
          </h1>
          <h2 className="text-sm/4 font-medium text-secondary">
            {categoryGroup !== "Other" && (
              <span>
                <span>{categoryGroup}</span>
                <span className="select-none">&#32;·&#32;</span>
              </span>
            )}
            <span>
              {numCeremonies} {numCeremonies !== 1 ? "ceremonies" : "ceremony"}
            </span>
            <span className="select-none">&#32;·&#32;</span>
            <span>
              {lastYear === 1927 + currentEdition
                ? firstYear + "-present"
                : firstYear === lastYear
                  ? firstYear
                  : firstYear + "-" + lastYear}
            </span>
          </h2>
        </div>
      </div>
      {children}
    </div>
  );
}
