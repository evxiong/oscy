import { TabGroup, TabList, Tab, TabPanels, TabPanel } from "@headlessui/react";
import {
  IconArrowLeft,
  IconArrowRight,
  IconLaurelWreath,
} from "@tabler/icons-react";
import {
  ceremonyToTopFive,
  dateToString,
  iterationToOrdinal,
  topFiveToImageUrls,
} from "@/app/_utils/utils";
import { AwardEnum, EditionType, NominationsType } from "./types";
import Link from "next/link";
import CeremonyStats from "./stats";
import Nominations from "@/app/_components/nominations";
import Breadcrumbs from "@/app/_components/breadcrumbs";
import AwardNavigator from "@/app/_components/awardNavigator";
import { SmallSelectorOption } from "@/app/_components/selectors";
import Card from "@/app/_components/card";
import { notFound } from "next/navigation";
import fetchError from "@/app/_utils/fetchError";
import { Metadata } from "next";

export async function generateStaticParams() {
  const editions: EditionType[] = await fetchError(
    "/api/ceremonies",
  );
  const iterations = editions.map((e) => ({
    iteration: e.iteration.toString(),
  }));
  return iterations;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ iteration: string }>;
}): Promise<Metadata> {
  const iteration = (await params).iteration;
  const nominations: NominationsType = await fetchError(
    `/api/?start_edition=${iteration}&end_edition=${iteration}`,
  );
  if (nominations === null || nominations.editions.length === 0) {
    notFound();
  }

  const ordinal = iterationToOrdinal(nominations.editions[0].iteration);
  const title = `${ordinal} Academy Awards - Nominations & Statistics`;
  const description = `Browse nominations and stats from the ${nominations.editions[0].official_year} (${ordinal}) Academy Awards.`;

  return {
    title: title,
    description: description,
    openGraph: {
      siteName: "oscy",
      title: title,
      description: description,
      type: "article",
      url: `/ceremony/${nominations.editions[0].iteration}`,
    },
    twitter: {
      card: "summary",
      title: title,
      description: description,
    },
  };
}

export default async function Ceremony({
  params,
}: {
  params: Promise<{ iteration: string }>;
}) {
  const iteration = (await params).iteration;
  const nominations: NominationsType = await fetchError(
    `/api/?start_edition=${iteration}&end_edition=${iteration}`,
  );

  if (nominations === null || nominations.editions.length === 0) {
    notFound();
  }

  const editions: EditionType[] = await fetchError(
    "/api/ceremonies",
  );
  const ceremony = nominations.editions[0];
  const ordinal = iterationToOrdinal(ceremony.iteration);
  const topFive = ceremonyToTopFive(nominations);
  const topFiveImageUrls: (string | null)[] = topFive
    ? await topFiveToImageUrls(topFive)
    : [null, null, null, null, null];

  const awardNavigatorOptions: SmallSelectorOption[] = editions.map((e) => ({
    id: e.iteration,
    name: e.official_year + " (" + iterationToOrdinal(e.iteration) + ")",
    disabled: false,
  }));
  const originalAwardNavigatorOption: SmallSelectorOption =
    awardNavigatorOptions[editions.findIndex((e) => e.id === ceremony.id)];

  return (
    <div className="flex flex-col gap-5">
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-5 px-6 pt-5 md:w-[768px]">
          <nav className="flex flex-row justify-between text-xs">
            <Breadcrumbs
              crumbs={[
                { name: "Home", link: "/" },
                { name: "Ceremony", link: "" },
              ]}
            />
            <AwardNavigator
              subdir="ceremony"
              originalAwardType={AwardEnum.oscar}
              options={awardNavigatorOptions}
              originalOption={originalAwardNavigatorOption}
            />
          </nav>
          <div className="flex w-full flex-row items-center justify-between">
            <div className="flex flex-col gap-1">
              <h1 className="text-2xl font-medium leading-7 text-zinc-800">
                {ordinal} Academy Awards
              </h1>
              <h2 className="text-sm font-medium leading-4 text-zinc-500">
                <span>{dateToString(ceremony.ceremony_date)}</span>
                <span className="select-none">&#32;·&#32;</span>
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
        {topFive ? (
          <div className="w-fit px-6 md:w-[768px]">
            <div className="flex flex-row gap-[11.25px]">
              {topFive.indices.map((catInd, i) => (
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
        ) : (
          <div className="flex min-h-56 items-center justify-center px-6 md:w-[768px]">
            <div className="flex select-none flex-row items-center gap-2 rounded-md border border-gray-200 px-4 py-2 text-sm font-medium text-gray-400">
              <IconLaurelWreath className="size-5" />
              <div>Winners TBD</div>
            </div>
          </div>
        )}
      </section>
      <section className="mb-20 flex w-full flex-col items-center">
        <div className="flex w-full px-6 md:w-[768px]">
          <TabGroup className="w-full">
            <TabList className="flex flex-row gap-7 text-lg font-medium text-zinc-500 sm:text-base sm:leading-7">
              <Tab className="decoration-zinc-500 underline-offset-[6px] focus:outline-none data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                Nominations
              </Tab>
              <Tab className="decoration-zinc-500 underline-offset-[6px] focus:outline-none data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
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
