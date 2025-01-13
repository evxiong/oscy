import Breadcrumbs from "@/app/_components/breadcrumbs";
import { Category, CategoryGroupInfo } from "./types";
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from "@headlessui/react";
import AwardNavigator from "@/app/_components/awardNavigator";
import { AwardType } from "@/app/ceremony/[iteration]/types";
import { SmallSelectorOption } from "@/app/_components/selectors";
import { categoryNamesToTimeline } from "@/app/_utils/utils";
import Nominations from "@/app/_components/nominations";

export default async function Category({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const categoryId = (await params).id;
  const categoriesData = await fetch("http://localhost:8000/categories");
  const categories: CategoryGroupInfo[] = await categoriesData.json();
  const categoryData = await fetch(
    `http://localhost:8000/category/${categoryId}`,
  );
  const category: Category = await categoryData.json();
  const categoryName = category.category.startsWith("Unique")
    ? category.category
    : "Best " + category.category;

  const awardNavigatorOptions: SmallSelectorOption[] = categories
    .map((categoryGroup) =>
      categoryGroup.categories.map((c) => ({
        id: c.category_id,
        name: c.category,
      })),
    )
    .flat();

  const originalAwardNavigatorOption: SmallSelectorOption =
    awardNavigatorOptions.find((e) => e.id === category.category_id)!;

  const timeline = categoryNamesToTimeline(category.category_names);
  const LATEST_EDITION = parseInt(process.env.LATEST_EDITION!);

  return (
    <div className="flex flex-col gap-5">
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-4 px-6 pt-5 md:w-[768px]">
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
            <div className="flex flex-col">
              <h1 className="text-2xl font-medium text-zinc-800">
                {categoryName}
              </h1>
              <h2 className="text-sm font-medium text-zinc-500">
                {category.category_group !== "Other" && (
                  <span>
                    <span>{category.category_group}</span>
                    <span className="select-none">&nbsp;·&nbsp;</span>
                  </span>
                )}
                <span className="text-red-500">x ceremonies</span>
                <span className="select-none">&nbsp;·&nbsp;</span>
                <span className="text-red-500">start-end</span>
              </h2>
            </div>
          </div>
        </div>
      </section>
      <section className="flex w-full flex-col overflow-x-auto bg-gradient-to-r from-white to-zinc-100 px-6 py-5 md:items-center">
        <div className="grid w-[720px] grid-flow-col justify-between">
          {/* {topFiveCategoryInds.map((catInd, i) => (
            <Card
              key={i}
              category={ceremony.categories[catInd]}
              imageUrl={topFiveImageUrls[i]}
            />
          ))} */}
        </div>
      </section>
      <section className="mb-20 flex w-full flex-col items-center">
        <div className="flex w-full px-6 md:w-[768px]">
          <TabGroup className="w-full">
            <TabList className="mb-0.5 flex flex-row gap-7 text-lg font-medium text-zinc-500 sm:text-base">
              <Tab className="decoration-zinc-500 underline-offset-[6px] data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                Nominations
              </Tab>
              <Tab className="decoration-zinc-500 underline-offset-[6px] data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                Statistics
              </Tab>
              <Tab className="decoration-zinc-500 underline-offset-[6px] data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                History
              </Tab>
            </TabList>
            <TabPanels>
              <TabPanel>
                {/* Better solution: pass editions to nominations, then have noms map it, pass boolean to display year or cat */}
                {/* Also allow passing search keys */}
                <Nominations
                  categories={category.nominations.editions
                    .map((e) => e.categories)
                    .flat()
                    .reverse()}
                  officialYear=""
                  ordinal=""
                />
              </TabPanel>
              <TabPanel>{/* <Stats stats={nominations.stats} /> */}</TabPanel>
              <TabPanel>
                <div className="sticky top-0 z-30 flex h-14 flex-row items-center justify-between gap-4 bg-white text-base font-medium text-zinc-500">
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
                          className={`${t.end_iteration === LATEST_EDITION ? "bg-gold" : "bg-zinc-300"} absolute -left-[5px] top-0 size-3 rounded-full`}
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
