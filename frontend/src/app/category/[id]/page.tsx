import Card from "@/app/_components/card";
import Nominations from "@/app/_components/nominations";
import { Tab, TabList, TabPanel, TabPanels, Tabs } from "@/app/_ui/Tabs";
import fetchError from "@/app/_utils/fetchError";
import {
  categoriesToTopFive,
  categoryNamesToTimeline,
  iterationToOrdinal,
  topFiveToImageUrls,
} from "@/app/_utils/utils";
import { Metadata } from "next";
import { notFound } from "next/navigation";
import CategoryStats from "./stats";
import type { Category } from "./types";

export async function generateStaticParams() {
  // const categoryGroups: CategoryGroupInfo[] =
  //   await fetchError("/api/categories");
  // const categoryIds = categoryGroups
  //   .map((categoryGroup) =>
  //     categoryGroup.categories.map((c) => ({
  //       id: c.category_id.toString(),
  //     })),
  //   )
  //   .flat();
  // return categoryIds;
  return [];
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const categoryId = (await params).id;
  const category: Category = await fetchError(`/api/categories/${categoryId}`);

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
  const category: Category = await fetchError(`/api/categories/${categoryId}`);

  if (category === null) {
    notFound();
  }

  const editions = category.nominations.editions.reverse();
  const nominationCategories = editions.map((e) => e.categories).flat();

  const topFive = categoriesToTopFive(nominationCategories);
  const topFiveImageUrls: (string | null)[] = await topFiveToImageUrls(topFive);

  const timeline = categoryNamesToTimeline(category.category_names);
  const LATEST_EDITION = parseInt(process.env.NEXT_PUBLIC_CURRENT_EDITION!);

  return (
    <>
      <div className="flex w-full flex-col overflow-x-auto bg-gradient-to-r from-white to-zinc-100 py-5 md:items-center">
        <div className="w-fit px-6 md:w-[768px]">
          <div className="flex flex-row gap-[11.25px]">
            {topFive.map((topFiveCard, i) => (
              <Card
                key={i}
                showCeremony={true}
                ceremony={
                  editions[topFiveCard.category_ind].official_year +
                  " (" +
                  iterationToOrdinal(
                    editions[topFiveCard.category_ind].iteration,
                  ) +
                  ")"
                }
                ceremonyId={editions[topFiveCard.category_ind].id}
                category={nominationCategories[topFiveCard.category_ind]}
                nominee={
                  nominationCategories[topFiveCard.category_ind].nominees[
                    topFiveCard.nominee_ind
                  ]
                }
                imageUrl={topFiveImageUrls[i]}
              />
            ))}
          </div>
        </div>
      </div>
      <div className="mb-20 flex w-full flex-col items-center">
        <div className="flex w-full px-6 md:w-[768px]">
          <Tabs className="w-full">
            <TabList>
              <Tab id="nominations">Nominations</Tab>
              <Tab id="statistics">Statistics</Tab>
              <Tab id="history">History</Tab>
            </TabList>
            <TabPanels>
              <TabPanel id="nominations" shouldForceMount>
                <Nominations
                  showCeremony={true}
                  editions={editions}
                  searchKeys={["year_and_ordinal", "common_name"]}
                />
              </TabPanel>
              <TabPanel id="statistics" shouldForceMount>
                <CategoryStats
                  entityStats={category.nominations.stats.entity_stats}
                />
              </TabPanel>
              <TabPanel id="history" shouldForceMount>
                <div className="flex h-14 flex-row items-center justify-between gap-4 bg-background text-sm font-medium text-secondary">
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
          </Tabs>
        </div>
      </div>
    </>
  );
}
