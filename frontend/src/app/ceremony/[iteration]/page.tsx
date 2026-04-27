import Card from "@/app/_components/card";
import Nominations from "@/app/_components/nominations";
import { Tab, TabList, TabPanel, TabPanels, Tabs } from "@/app/_ui/Tabs";
import { fetchApi } from "@/app/_utils/fetch";
import {
  ceremonyToTopFive,
  iterationToOrdinal,
  topFiveToImageUrls,
} from "@/app/_utils/utils";
import { IconLaurelWreath } from "@tabler/icons-react";
import { Metadata } from "next";
import { notFound } from "next/navigation";
import CeremonyEntityStats from "./CeremonyEntityStats";
import CeremonyTitleStats from "./CeremonyTitleStats";
import { NominationsType } from "./types";

export async function generateStaticParams() {
  // const editions: EditionType[] = await fetchApi(
  //   "/ceremonies",
  // );
  // const iterations = editions.map((e) => ({
  //   iteration: e.iteration.toString(),
  // }));
  // return iterations;
  return [];
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ iteration: string }>;
}): Promise<Metadata> {
  const iteration = (await params).iteration;
  const nominations: NominationsType = await fetchApi(
    `/?start_edition=${iteration}&end_edition=${iteration}`,
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
  const nominations: NominationsType = await fetchApi(
    `/?start_edition=${iteration}&end_edition=${iteration}`,
  );

  if (nominations === null || nominations.editions.length === 0) {
    notFound();
  }

  const ceremony = nominations.editions[0];
  const ordinal = iterationToOrdinal(ceremony.iteration);
  const topFive = ceremonyToTopFive(nominations);
  const topFiveImageUrls: (string | null)[] = topFive
    ? await topFiveToImageUrls(topFive)
    : [null, null, null, null, null];

  return (
    <>
      <div className="flex w-full flex-col overflow-x-auto bg-gradient-to-r from-white to-zinc-100 py-5 md:items-center">
        {topFive ? (
          <div className="w-fit px-6 md:w-[768px]">
            <div className="flex flex-row gap-[11.25px]">
              {topFive.map((topFiveCard, i) => (
                <Card
                  key={i}
                  showCeremony={false}
                  ceremony={ceremony.official_year + " (" + ordinal + ")"}
                  ceremonyId={ceremony.iteration}
                  category={ceremony.categories[topFiveCard.category_ind]}
                  nominee={
                    ceremony.categories[topFiveCard.category_ind].nominees[
                      topFiveCard.nominee_ind
                    ]
                  }
                  imageUrl={topFiveImageUrls[i]}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="flex min-h-56 items-center justify-center px-6 md:w-[768px]">
            <div className="flex select-none flex-row items-center gap-2 rounded-md border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-400">
              <IconLaurelWreath className="size-5" />
              <div>Winners TBD</div>
            </div>
          </div>
        )}
      </div>
      <div className="mb-20 flex w-full flex-col items-center">
        <div className="flex w-full px-6 md:w-[768px]">
          <Tabs className="w-full">
            <TabList>
              <Tab id="nominations">Nominations</Tab>
              <Tab id="films">Films</Tab>
              <Tab id="people">People</Tab>
            </TabList>
            <TabPanels>
              <TabPanel id="nominations" shouldForceMount>
                <Nominations
                  showCeremony={false}
                  editions={nominations.editions}
                  searchKeys={[
                    "category_group",
                    "official_name",
                    "common_name",
                    "short_name",
                  ]}
                />
              </TabPanel>
              <TabPanel id="films" shouldForceMount>
                <CeremonyTitleStats stats={nominations.stats} />
              </TabPanel>
              <TabPanel id="people" shouldForceMount>
                <CeremonyEntityStats stats={nominations.stats} />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </div>
      </div>
    </>
  );
}
