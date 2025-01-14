import Breadcrumbs from "@/app/_components/breadcrumbs";
import { imdbIdToUrl } from "@/app/_utils/utils";
import { IconArrowUpRight } from "@tabler/icons-react";
import { Entity } from "./types";
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from "@headlessui/react";
import Nominations from "@/app/_components/nominations";

export default async function Entity({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const entityId = (await params).id;
  const entityData = await fetch(`http://localhost:8000/entity/${entityId}`);
  const entity: Entity = await entityData.json();

  const validImdbId =
    !entity.imdb_id.startsWith("cc") && entity.imdb_id[2] !== "_";
  const imdbUrl = validImdbId ? imdbIdToUrl(entity.imdb_id) : "";

  return (
    <div className="flex flex-col gap-5">
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-4 px-6 pt-5 md:w-[768px]">
          <nav className="flex flex-row justify-between text-xs">
            <Breadcrumbs
              crumbs={[
                { name: "Home", link: "/" },
                { name: "Entity", link: "" },
              ]}
            />
            {validImdbId && (
              <a
                target="_blank"
                rel="noopener noreferrer"
                href={imdbUrl}
                className="group flex cursor-pointer flex-row items-center text-xs font-medium text-zinc-500 underline decoration-zinc-300 underline-offset-4 hover:text-zinc-600 hover:decoration-zinc-400"
              >
                <div>IMDb</div>
                <IconArrowUpRight className="size-3.5" />
              </a>
            )}
          </nav>
        </div>
      </section>
      <section className="flex w-full flex-col items-center bg-gradient-to-r from-white to-zinc-100 py-7">
        <div className="flex w-full flex-col gap-6 px-6 sm:flex-row sm:items-center md:w-[768px]">
          <div className="flex flex-1 flex-col gap-0.5">
            <h1 className="text-2xl font-medium leading-7 text-zinc-800">
              {entity.name}
            </h1>
            <h2 className="text-sm font-medium text-zinc-500">
              {entity.total_noms}{" "}
              {entity.total_noms > 1 ? "nominations" : "nomination"}
              <span className="select-none">&nbsp;·&nbsp;</span>
              {entity.total_wins} {entity.total_wins > 1 ? "wins" : "win"}
            </h2>
          </div>
          <div className="flex flex-1 flex-row gap-4">
            <div className="flex flex-1 flex-col gap-1">
              <div className="text-xxs font-semibold text-zinc-800">
                ACADEMY AWARDS
              </div>
              <div className="flex flex-col gap-0 text-xl font-medium leading-6 text-zinc-500">
                <div>
                  {entity.total_noms} {entity.total_noms > 1 ? "noms" : "nom"}
                </div>
                <div>
                  {entity.total_wins} {entity.total_wins > 1 ? "wins" : "win"}
                </div>
              </div>
            </div>
            <div className="flex-1"></div>
          </div>
        </div>
      </section>
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full px-6 md:w-[768px]">Also known as</div>
      </section>
      <section className="mb-20 flex w-full flex-col items-center">
        <div className="flex w-full px-6 md:w-[768px]">
          <TabGroup className="w-full">
            <TabList className="mb-0.5 flex flex-row gap-7 text-lg font-medium text-zinc-500 sm:text-base">
              <Tab className="decoration-zinc-500 underline-offset-[6px] data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                Nominations
              </Tab>
              <Tab className="decoration-zinc-500 underline-offset-[6px] data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                Rankings
              </Tab>
            </TabList>
            <TabPanels>
              <TabPanel>
                <Nominations
                  showCeremony={true}
                  editions={entity.nominations.reverse()}
                  searchHeader="Ceremony"
                  searchKeys={["year_and_ordinal", "common_name"]}
                  stickyHeader=""
                />
              </TabPanel>
              <TabPanel>
                {/* <CategoryStats
                  entityStats={category.nominations.stats.entity_stats}
                /> */}
              </TabPanel>
            </TabPanels>
          </TabGroup>
        </div>
      </section>
    </div>
  );
}
