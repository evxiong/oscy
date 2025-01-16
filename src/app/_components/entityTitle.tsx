import { IconArrowUpRight } from "@tabler/icons-react";
import Breadcrumbs from "./breadcrumbs";
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from "@headlessui/react";
import AggregateNominations from "../entity/[id]/aggNominations";
import Rankings from "../entity/[id]/rankings";
import { EntityOrTitle } from "../entity/[id]/types";
import { imdbIdToUrl } from "../_utils/utils";

export default function EntityTitle({
  isTitle,
  entityOrTitle,
}: {
  isTitle: boolean;
  entityOrTitle: EntityOrTitle;
}) {
  const aliases = entityOrTitle.aliases.filter((a) => a !== entityOrTitle.name);
  const validImdbId =
    !entityOrTitle.imdb_id.startsWith("cc") && entityOrTitle.imdb_id[2] !== "_";
  const imdbUrl = validImdbId ? imdbIdToUrl(entityOrTitle.imdb_id) : "";

  return (
    <div className="flex flex-col gap-5">
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-4 px-6 pt-5 md:w-[768px]">
          <nav className="flex flex-row justify-between text-xs">
            <Breadcrumbs
              crumbs={
                isTitle
                  ? [
                      { name: "Home", link: "/" },
                      { name: "Title", link: "" },
                    ]
                  : [
                      { name: "Home", link: "/" },
                      { name: "Entity", link: "" },
                    ]
              }
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
            <h1
              className={`${isTitle ? "italic" : ""} text-2xl font-medium leading-7 text-zinc-800 sm:pr-4`}
            >
              {entityOrTitle.name}
            </h1>
            <h2 className="text-sm font-medium text-zinc-500">
              <span>
                {entityOrTitle.total_noms}&nbsp;
                {entityOrTitle.total_noms !== 1 ? "nominations" : "nomination"}
                <span className="select-none">&nbsp;·&nbsp;</span>
                {entityOrTitle.total_wins}&nbsp;
                {entityOrTitle.total_wins !== 1 ? "wins" : "win"}
              </span>
            </h2>
          </div>
          <div className="flex flex-1 flex-row gap-4">
            <div className="flex flex-1 flex-col gap-1">
              <div className="text-xxs font-semibold text-zinc-800">
                ACADEMY AWARDS
              </div>
              <div className="flex flex-col gap-0 text-xl font-medium leading-6 text-zinc-500">
                <div>
                  {entityOrTitle.total_noms}{" "}
                  {entityOrTitle.total_noms !== 1 ? "noms" : "nom"}
                </div>
                <div>
                  {entityOrTitle.total_wins}{" "}
                  {entityOrTitle.total_wins !== 1 ? "wins" : "win"}
                </div>
              </div>
            </div>
            <div className="flex-1"></div>
          </div>
        </div>
      </section>
      {!isTitle && aliases.length > 0 && (
        <section className="flex w-full flex-col items-center">
          <div className="flex w-full flex-col gap-4 px-6 pb-4 md:w-[768px]">
            <div className="flex w-full flex-col gap-2 border-zinc-200 font-medium sm:flex-row sm:gap-6">
              <div className="flex-1 text-sm font-medium leading-4 text-zinc-500">
                <p className="mb-1 font-semibold">Also known as</p>
                <p>
                  {aliases.map((a, i) => (
                    <span key={i}>
                      <span>{a}</span>
                      {i < aliases.length - 1 && ", "}
                    </span>
                  ))}
                </p>
              </div>
            </div>
          </div>
        </section>
      )}
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
                <AggregateNominations
                  editions={entityOrTitle.nominations.reverse()}
                  searchHeader="Category"
                  stickyHeader=""
                />
              </TabPanel>
              <TabPanel>
                <Rankings
                  overallRankings={entityOrTitle.rankings.overall_rankings}
                  categoryRankings={entityOrTitle.rankings.category_rankings}
                  categoryGroupRankings={
                    entityOrTitle.rankings.category_group_rankings
                  }
                />
              </TabPanel>
            </TabPanels>
          </TabGroup>
        </div>
      </section>
    </div>
  );
}
