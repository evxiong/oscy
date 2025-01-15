import { TabGroup, TabList, Tab, TabPanels, TabPanel } from "@headlessui/react";
import { IconArrowLeft, IconArrowRight } from "@tabler/icons-react";
import {
  ceremonyToTopFive,
  dateToString,
  iterationToOrdinal,
  topFiveToImageUrls,
} from "@/app/_utils/utils";
import { AwardType, EditionType, NominationsType } from "./types";
import Link from "next/link";
import CeremonyStats from "./stats";
import Nominations from "@/app/_components/nominations";
import Breadcrumbs from "@/app/_components/breadcrumbs";
import AwardNavigator from "@/app/_components/awardNavigator";
import { SmallSelectorOption } from "@/app/_components/selectors";
import Card from "@/app/_components/card";

export default async function Ceremony({
  params,
}: {
  params: Promise<{ iteration: string }>;
}) {
  const iteration = (await params).iteration;
  const nominationsData = await fetch(
    `http://localhost:8000/?start_edition=${iteration}&end_edition=${iteration}`,
  );
  const nominations: NominationsType = await nominationsData.json();
  const editionsData = await fetch("http://localhost:8000/editions");
  const editions: EditionType[] = await editionsData.json();
  const ceremony = nominations.editions[0];
  const ordinal = iterationToOrdinal(ceremony.iteration);
  const topFive = ceremonyToTopFive(nominations);
  const topFiveCategoryInds: number[] = topFive.indices;
  const topFiveImageUrls: (string | null)[] = await topFiveToImageUrls(topFive);

  const awardNavigatorOptions: SmallSelectorOption[] = editions.map((e) => ({
    id: e.iteration,
    name: e.official_year + " (" + iterationToOrdinal(e.iteration) + ")",
  }));
  const originalAwardNavigatorOption: SmallSelectorOption =
    awardNavigatorOptions[editions.findIndex((e) => e.id === ceremony.id)];

  return (
    <div className="flex flex-col gap-5">
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-4 px-6 pt-5 md:w-[768px]">
          <nav className="flex flex-row justify-between text-xs">
            <Breadcrumbs
              crumbs={[
                { name: "Home", link: "/" },
                { name: "Ceremony", link: "" },
              ]}
            />
            <AwardNavigator
              subdir="ceremony"
              originalAwardType={AwardType.oscar}
              options={awardNavigatorOptions}
              originalOption={originalAwardNavigatorOption}
            />
          </nav>
          <div className="flex w-full flex-row items-center justify-between">
            <div className="flex flex-col">
              <h1 className="text-2xl font-medium text-zinc-800">
                {ordinal} Academy Awards
              </h1>
              <h2 className="text-sm font-medium text-zinc-500">
                <span>{dateToString(ceremony.ceremony_date)}</span>
                <span className="select-none">&nbsp;·&nbsp;</span>
                <span>Honoring films from {ceremony.official_year}</span>
              </h2>
            </div>
            <div className="hidden flex-row gap-2 sm:flex">
              <Link
                href={`/ceremony/${ceremony.iteration - 1}`}
                className={`${ceremony.iteration === 1 ? "hidden" : "flex"} h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-zinc-100 hover:bg-zinc-200`}
              >
                <IconArrowLeft className="h-5 w-5 stroke-zinc-500" />
              </Link>
              <Link
                href={`/ceremony/${ceremony.iteration + 1}`}
                className={`${ceremony.iteration === editions.length ? "hidden" : "flex"} h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-zinc-100 hover:bg-zinc-200`}
              >
                <IconArrowRight className="h-5 w-5 stroke-zinc-500" />
              </Link>
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
                showCeremony={false}
                ceremony={ceremony.official_year + " (" + ordinal + ")"}
                ceremonyId={ceremony.iteration}
                category={ceremony.categories[catInd]}
                imageUrl={topFiveImageUrls[i]}
              />
            ))}
          </div>
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
            </TabList>
            <TabPanels>
              <TabPanel>
                <Nominations
                  showCeremony={false}
                  editions={nominations.editions}
                  searchHeader="Category"
                  searchKeys={[
                    "category_group",
                    "official_name",
                    "common_name",
                    "short_name",
                  ]}
                  stickyHeader={ceremony.official_year + " (" + ordinal + ")"}
                />
              </TabPanel>
              <TabPanel>
                <CeremonyStats stats={nominations.stats} />
              </TabPanel>
            </TabPanels>
          </TabGroup>
        </div>
      </section>
    </div>
  );
}
