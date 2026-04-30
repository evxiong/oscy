import Nominations from "@/app/_components/Nominations";
import TopFiveCard from "@/app/_components/TopFiveCard";
import { Tab, TabList, TabPanel, TabPanels, Tabs } from "@/app/_ui/Tabs";
import { fetchApi, fetchVersion } from "@/app/_utils/fetch";
import merge from "@/app/_utils/merge";
import { categoriesToTopFive, topFiveToImageUrls } from "@/app/_utils/topFive";
import {
  categoryNamesToTimeline,
  iterationToOrdinal,
} from "@/app/_utils/utils";
import { Metadata } from "next";
import { notFound } from "next/navigation";
import CategoryStats from "./CategoryStats";
import type { Category } from "./types";

export async function generateStaticParams() {
  // const categoryGroups: CategoryGroupInfo[] =
  //   await fetchApi("/categories");
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
  const category: Category = await fetchApi(`/categories/${categoryId}`);

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
  const category: Category = await fetchApi(`/categories/${categoryId}`);

  if (category === null) {
    notFound();
  }

  const editions = category.nominations.editions.reverse();
  const nominationCategories = editions.map((e) => e.categories).flat();

  const topFive = categoriesToTopFive(nominationCategories);
  const topFiveImageUrls = await topFiveToImageUrls(topFive);

  const timeline = categoryNamesToTimeline(category.category_names);

  const currentEdition = (await fetchVersion()).iteration;

  return (
    <>
      <div className="flex w-full flex-col overflow-x-auto bg-gradient-to-r from-background to-overlay py-5 md:items-center">
        <div className="w-fit px-6 md:w-[768px]">
          <div className="flex flex-row gap-[11.25px]">
            {topFive.map((topFiveCard, i) => (
              <TopFiveCard
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
                  {/* {timeline[0].end_iteration === currentEdition && (
                    <div className="relative ml-4 h-6">
                      <div className="before:absolute before:bottom-0 before:left-0 before:top-0 before:border-l-2 before:border-gold before:content-['']"></div>
                    </div>
                  )} */}
                  {timeline.map((t, i) => (
                    <div key={i} className="relative ml-4">
                      <div
                        className={merge(
                          t.start_iteration === 1
                            ? "before:border-none"
                            : i < timeline.length - 1 &&
                                t.start_iteration ===
                                  timeline[i + 1].end_iteration + 1
                              ? "before:border-solid"
                              : "before:border-dashed",
                          "w-full pb-6 before:absolute before:bottom-0 before:left-0 before:top-0 before:border-l-2 before:border-underline before:content-['']",
                        )}
                      >
                        <div
                          className={`${t.end_iteration === currentEdition ? "border-4 border-gold" : "border-2 border-underline"} absolute -left-[5px] top-0 size-3 rounded-full bg-background`}
                        ></div>
                        <div className="-mt-1 flex flex-col gap-0.5 pl-6">
                          <div
                            className={`${t.end_iteration === currentEdition ? "text-primary" : "text-subtitle"} text-base/5`}
                          >
                            {t.name}
                          </div>
                          <div
                            className={`${t.end_iteration === currentEdition ? "text-primary" : "text-secondary"} text-sm font-normal`}
                          >
                            {t.end_iteration === currentEdition
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
