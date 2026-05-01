import { IconArrowUpRight } from "@tabler/icons-react";
import { Fragment } from "react";
import Skeleton from "../_ui/Skeleton";
import { Tab, TabList, TabPanel, TabPanels, Tabs } from "../_ui/Tabs";
import { imdbIdToUrl } from "../_utils/utils";
import { EntityOrTitle } from "../entity/[id]/types";
import AggregateNominations from "./AggregateNominations";
import Breadcrumbs from "./Breadcrumbs";
import ExternalLink from "./ExternalLink";
import Rankings from "./Rankings";

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
      <div className="flex w-full flex-col items-center">
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
              <ExternalLink
                href={imdbUrl}
                className="group flex cursor-pointer flex-row items-center text-xs font-medium text-secondary underline decoration-underline underline-offset-4 hover:text-subtitle hover:decoration-tertiary"
              >
                <span>IMDb</span>
                <IconArrowUpRight aria-hidden className="size-3.5" />
              </ExternalLink>
            )}
          </nav>
        </div>
      </div>
      <div className="flex w-full flex-col items-center bg-gradient-to-r from-background to-overlay py-7">
        <div className="flex w-full flex-col gap-6 px-6 sm:flex-row sm:items-center md:w-[768px]">
          <div className="flex flex-1 flex-col gap-0.5">
            <h1
              className={`${isTitle ? "italic" : ""} text-2xl/7 font-medium text-primary sm:pr-4`}
            >
              {entityOrTitle.name}
            </h1>
            <h2 className="text-sm font-medium text-secondary">
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
              <div className="text-xxs font-semibold text-primary">
                ACADEMY AWARDS
              </div>
              <div className="flex flex-col gap-0 text-xl/6 font-medium text-secondary">
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
      </div>
      {!isTitle && aliases.length > 0 && (
        <div className="flex w-full flex-col items-center">
          <div className="flex w-full flex-col gap-4 px-6 pb-4 md:w-[768px]">
            <div className="flex w-full flex-col gap-2 border-border font-medium sm:flex-row sm:gap-6">
              <div className="flex-1 text-sm/4 font-medium text-secondary">
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
        </div>
      )}
      <div className="mb-20 flex w-full flex-col items-center">
        <div className="flex w-full px-6 md:w-[768px]">
          <Tabs className="w-full">
            <TabList>
              <Tab id="nominations">Nominations</Tab>
              <Tab id="statistics">Statistics</Tab>
            </TabList>
            <TabPanels>
              <TabPanel id="nominations" shouldForceMount>
                <AggregateNominations
                  editions={entityOrTitle.nominations.reverse()}
                />
              </TabPanel>
              <TabPanel id="statistics" shouldForceMount>
                <Rankings
                  overallRankings={entityOrTitle.rankings.overall_rankings}
                  categoryRankings={entityOrTitle.rankings.category_rankings}
                  categoryGroupRankings={
                    entityOrTitle.rankings.category_group_rankings
                  }
                />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

export function EntityTitleLoading() {
  return (
    <div className="flex flex-col gap-5">
      <div className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-4 px-6 pt-5 md:w-[768px]">
          <nav className="flex flex-row justify-between">
            <div className="flex h-5 items-center">
              <Skeleton className="h-3 w-16" />
            </div>
            <div className="flex h-5 items-center">
              <Skeleton className="h-3 w-10" />
            </div>
          </nav>
        </div>
      </div>
      <div className="flex w-full flex-col items-center bg-gradient-to-r from-background to-overlay py-7">
        <div className="flex w-full flex-col gap-6 px-6 sm:flex-row sm:items-center md:w-[768px]">
          <div className="flex flex-1 flex-col gap-0.5">
            <div className="flex h-7 items-center sm:pr-4">
              <Skeleton className="h-6 w-28" />
            </div>
            <h2 className="flex h-5 items-center">
              <Skeleton className="h-3.5 w-48" />
            </h2>
          </div>
          <div className="flex flex-1 flex-row gap-4">
            <div className="flex flex-1 flex-col gap-1">
              <div className="flex h-3 items-center">
                <Skeleton className="h-2.5 w-20" />
              </div>
              <div className="flex flex-col">
                <div className="flex h-6 items-center">
                  <Skeleton className="h-5 w-14" />
                </div>
                <div className="flex h-6 items-center">
                  <Skeleton className="h-5 w-14" />
                </div>
              </div>
            </div>
            <div className="flex-1"></div>
          </div>
        </div>
      </div>
      <div className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-4 px-6 pb-4 md:w-[768px]">
          <div className="flex w-full flex-col gap-2 border-border sm:flex-row sm:gap-6">
            <div className="flex-1">
              <div className="mb-1 flex h-4 items-center">
                <Skeleton className="h-3.5 w-24" />
              </div>
              <div className="flex h-4 items-center">
                <Skeleton className="h-3.5 w-48" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="mb-20 flex w-full flex-col items-center">
        <div className="w-full px-6 md:w-[768px]">
          <Skeleton className="-mb-2 h-4 w-60" />
          <div className="hide-scrollbar sticky top-0 z-30 flex h-[--nominations-header-height-mobile] flex-col justify-center gap-3 overflow-x-auto sm:h-[--nominations-header-height] sm:flex-row sm:items-center sm:gap-6">
            <div className="sm:flex-1">
              <Skeleton className="h-6 w-full" />
            </div>
            <div className="flex sm:flex-1 sm:justify-end">
              <Skeleton className="h-4 w-32" />
            </div>
          </div>
          <hr />
          {[...Array(4)].map((_, i) => (
            <Fragment key={i}>
              <div className="flex flex-col gap-1 py-6 sm:flex-row sm:gap-6">
                <div className="sticky top-[--nominations-header-height-mobile] z-10 w-full flex-1 bg-background pb-4 sm:top-[--nominations-header-height] sm:pb-0">
                  <div className="sticky top-[--nominations-header-height-mobile] z-10 sm:top-[--nominations-header-height]">
                    <Skeleton className="h-6 w-24" />
                    <div className="mt-1 flex h-4 items-center">
                      <Skeleton className="h-3.5 w-48" />
                    </div>
                  </div>
                </div>
                <div className="flex flex-1 flex-col gap-[0.875rem]">
                  {[...Array(5)].map((_, j) => (
                    <div key={j} className="flex flex-row gap-2.5">
                      <div className="size-4 shrink-0" />
                      <div className="flex flex-col gap-1">
                        <div className="flex h-5 items-center">
                          <Skeleton className="h-4 w-24" />
                        </div>
                        <div className="flex h-4 items-center">
                          <Skeleton className="h-3.5 w-64" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <hr />
            </Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}
