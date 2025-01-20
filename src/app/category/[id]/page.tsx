import Breadcrumbs from "@/app/_components/breadcrumbs";
import { Category, CategoryGroupInfo } from "./types";
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from "@headlessui/react";
import AwardNavigator from "@/app/_components/awardNavigator";
import { AwardType } from "@/app/ceremony/[iteration]/types";
import { SmallSelectorOption } from "@/app/_components/selectors";
import {
  categoriesToTopFive,
  categoryNamesToTimeline,
  iterationToOrdinal,
  topFiveToImageUrls,
} from "@/app/_utils/utils";
import Nominations from "@/app/_components/nominations";
import Card from "@/app/_components/card";
import CategoryStats from "./stats";
import { notFound } from "next/navigation";
import fetchError from "@/app/_utils/fetchError";
import { Metadata } from "next";

export async function generateStaticParams() {
  const categoryGroups: CategoryGroupInfo[] = await fetchError(
    "http://localhost:8000/categories",
  );
  const categoryIds = categoryGroups
    .map((categoryGroup) =>
      categoryGroup.categories.map((c) => ({
        id: c.category_id.toString(),
      })),
    )
    .flat();
  return categoryIds;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const categoryId = (await params).id;
  const category: Category = await fetchError(
    `http://localhost:8000/category/${categoryId}`,
  );

  if (category === null) {
    notFound();
  }

  const categoryName = category.category.startsWith("Unique")
    ? category.category
    : "Best " + category.category;

  const title = `${categoryName} - Nominations & Statistics`;
  const description = `Browse nominations and stats in the ${categoryName} category.`;

  return {
    title: title,
    description: description,
    openGraph: {
      siteName: "oscy",
      title: title,
      description: description,
      type: "article",
      url: `/category/${category.category_id}`,
    },
    twitter: {
      card: "summary",
      title: title,
      description: description,
    },
  };
}

export default async function Category({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const categoryId = (await params).id;
  const category: Category = await fetchError(
    `http://localhost:8000/category/${categoryId}`,
  );

  if (category === null) {
    notFound();
  }

  const categories: CategoryGroupInfo[] = await fetchError(
    "http://localhost:8000/categories",
  );
  const editions = category.nominations.editions.reverse();
  const nominationCategories = editions.map((e) => e.categories).flat();

  const topFive = categoriesToTopFive(nominationCategories);
  const topFiveCategoryInds: number[] = topFive.indices;
  const topFiveImageUrls: (string | null)[] = await topFiveToImageUrls(topFive);

  const categoryName = category.category.startsWith("Unique")
    ? category.category
    : "Best " + category.category;

  const awardNavigatorOptions: SmallSelectorOption[] = categories
    .map((categoryGroup) =>
      categoryGroup.categories.map((c) => ({
        id: c.category_id,
        name: c.category,
        disabled: false,
      })),
    )
    .flat();

  const originalAwardNavigatorOption: SmallSelectorOption =
    awardNavigatorOptions.find((e) => e.id === category.category_id)!;

  const timeline = categoryNamesToTimeline(category.category_names);
  const LATEST_EDITION = parseInt(process.env.NEXT_PUBLIC_LATEST_EDITION!);
  const numCeremonies = category.category_names.reduce(
    (acc1, cn) =>
      acc1 + cn.ranges.reduce((acc2, r) => acc2 + r[1] - r[0] + 1, 0),
    0,
  );
  const firstYear = timeline.at(-1)!.start_year;
  const lastYear = timeline[0].end_year;

  return (
    <div className="flex flex-col gap-5">
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-5 px-6 pt-5 md:w-[768px]">
          <nav className="flex flex-row justify-between text-xs">
            <Breadcrumbs
              crumbs={[
                { name: "Home", link: "/" },
                { name: "Category", link: "" },
              ]}
            />
            <AwardNavigator
              subdir="category"
              originalAwardType={AwardType.oscar}
              options={awardNavigatorOptions}
              originalOption={originalAwardNavigatorOption}
            />
          </nav>
          <div className="flex w-full flex-row items-center justify-between">
            <div className="flex flex-col gap-1">
              <h1 className="text-2xl font-medium leading-7 text-zinc-800">
                {categoryName}
              </h1>
              <h2 className="text-sm font-medium leading-4 text-zinc-500">
                {category.category_group !== "Other" && (
                  <span>
                    <span>{category.category_group}</span>
                    <span className="select-none">&#32;·&#32;</span>
                  </span>
                )}
                <span>
                  {numCeremonies}{" "}
                  {numCeremonies !== 1 ? "ceremonies" : "ceremony"}
                </span>
                <span className="select-none">&#32;·&#32;</span>
                <span>
                  {lastYear === 1927 + LATEST_EDITION
                    ? firstYear + "-present"
                    : firstYear === lastYear
                      ? firstYear
                      : firstYear + "-" + lastYear}
                </span>
              </h2>
            </div>
          </div>
        </div>
      </section>
      <section className="flex w-full flex-col overflow-x-auto bg-gradient-to-r from-white to-zinc-100 py-5 md:items-center">
        <div className="w-fit px-6 md:w-[768px]">
          <div className="flex flex-row gap-[11.25px]">
            {topFiveCategoryInds.map((catInd, i) => (
              <Card
                key={i}
                showCeremony={true}
                ceremony={
                  editions[i].official_year +
                  " (" +
                  iterationToOrdinal(editions[i].iteration) +
                  ")"
                }
                ceremonyId={editions[i].id}
                category={nominationCategories[catInd]}
                imageUrl={topFiveImageUrls[i]}
              />
            ))}
          </div>
        </div>
      </section>
      <section className="mb-20 flex w-full flex-col items-center">
        <div className="flex w-full px-6 md:w-[768px]">
          <TabGroup className="w-full">
            <TabList
              id="hide-scrollbar"
              className="flex flex-row gap-7 overflow-x-auto text-lg font-medium text-zinc-500 sm:text-base sm:leading-7"
            >
              <Tab className="decoration-zinc-500 underline-offset-[6px] focus:outline-none data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                Nominations
              </Tab>
              <Tab className="decoration-zinc-500 underline-offset-[6px] focus:outline-none data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                Statistics
              </Tab>
              <Tab className="decoration-zinc-500 underline-offset-[6px] focus:outline-none data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                History
              </Tab>
            </TabList>
            <TabPanels>
              <TabPanel>
                <Nominations
                  showCeremony={true}
                  editions={editions}
                  searchHeader="Ceremony"
                  searchKeys={["year_and_ordinal", "common_name"]}
                  stickyHeader={category.category}
                />
              </TabPanel>
              <TabPanel>
                <CategoryStats
                  entityStats={category.nominations.stats.entity_stats}
                />
              </TabPanel>
              <TabPanel>
                <div className="flex h-14 flex-row items-center justify-between gap-4 bg-white text-base font-medium text-zinc-500">
                  <div>Known as</div>
                </div>
                <div className="flex flex-col font-medium">
                  {/* {timeline[0].end_iteration === LATEST_EDITION && (
                    <div className="relative ml-4 h-6">
                      <div className="before:absolute before:bottom-0 before:left-0 before:top-0 before:border-l-2 before:border-gold before:content-['']"></div>
                    </div>
                  )} */}
                  {timeline.map((t, i) => (
                    <div key={i} className="relative ml-4">
                      <div
                        className={`${t.start_iteration === 1 ? "before:border-none" : i < timeline.length - 1 && t.start_iteration === timeline[i + 1].end_iteration + 1 ? "before:border-solid" : "before:border-dashed"} w-full pb-6 before:absolute before:bottom-0 before:left-0 before:top-0 before:border-l-2 before:border-zinc-300 before:content-['']`}
                      >
                        <div
                          className={`${t.end_iteration === LATEST_EDITION ? "border-4 border-gold" : "border-2 border-zinc-300"} absolute -left-[5px] top-0 size-3 rounded-full bg-white`}
                        ></div>
                        <div className="-mt-1 flex flex-col gap-0.5 pl-6">
                          <div
                            className={`${t.end_iteration === LATEST_EDITION ? "text-zinc-800" : "text-zinc-600"} text-base leading-5`}
                          >
                            {t.name}
                          </div>
                          <div
                            className={`${t.end_iteration === LATEST_EDITION ? "text-zinc-800" : "text-zinc-500"} text-sm font-normal`}
                          >
                            {t.end_iteration === LATEST_EDITION
                              ? t.start_year + "-present"
                              : t.start_year === t.end_year
                                ? t.start_year
                                : t.start_year + "-" + t.end_year}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </TabPanel>
            </TabPanels>
          </TabGroup>
        </div>
      </section>
    </div>
  );
}
