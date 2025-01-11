import {
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Input,
} from "@headlessui/react";
import {
  IconStarFilled,
  IconArrowLeft,
  IconArrowRight,
} from "@tabler/icons-react";
import { ceremonyToTopFive, iterationToOrdinal } from "@/app/_utils/utils";
import { CategoryType, NomineeType, NominationsType } from "./types";
import Image from "next/image";
import Link from "next/link";
import Stats from "./stats";

export default async function Ceremony({
  params,
}: {
  params: Promise<{ iteration: string }>;
}) {
  const iteration = (await params).iteration;
  const data = await fetch(
    `http://localhost:8000/?start_edition=${iteration}&end_edition=${iteration}`,
  );
  const nominations: NominationsType = await data.json();
  const ceremony = nominations.editions[0];
  const ordinal = iterationToOrdinal(ceremony.iteration);
  const topFive = ceremonyToTopFive(nominations);
  const topFiveCategoryInds: number[] = topFive.indices;
  const topFiveImageUrls: string[] = await Promise.all(
    topFive.imdb_ids.map(async (imdb_id) => {
      let res = await fetch(
        `https://api.themoviedb.org/3/find/${imdb_id}?external_source=imdb_id&api_key=${process.env.TMDB_API_KEY}`,
      );
      res = await res.json();
      if (imdb_id.startsWith("tt")) {
        return (
          "https://image.tmdb.org/t/p/w185" +
          // @ts-ignore
          res["movie_results"][0]["poster_path"]
        );
      } else {
        return (
          "https://image.tmdb.org/t/p/w185" +
          // @ts-ignore
          res["person_results"][0]["profile_path"]
        );
      }
    }),
  );

  return (
    <div className="flex flex-col gap-5">
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-4 px-6 pt-5 md:w-[768px]">
          <nav className="flex flex-row justify-between text-xs font-medium text-zinc-500 underline decoration-zinc-300 underline-offset-4">
            <div>Ceremony</div>
            <div className="flex flex-row gap-4">
              <div>Academy Awards</div>
              <div>
                {ceremony.official_year} ({ordinal})
              </div>
            </div>
          </nav>
          <div className="flex w-full flex-row items-center justify-between">
            <div className="flex flex-col">
              <h1 className="text-2xl font-medium text-zinc-800">
                {ordinal} Academy Awards
              </h1>
              <h2 className="text-sm font-medium text-zinc-500">
                <span>
                  {new Date(ceremony.ceremony_date).toLocaleDateString(
                    "en-US",
                    {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      timeZone: "UTC",
                    },
                  )}
                </span>
                <span className="select-none">&nbsp;·&nbsp;</span>
                <span>Honoring films from {ceremony.official_year}</span>
              </h2>
            </div>
            <div className="hidden flex-row gap-2 sm:flex">
              <div className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-zinc-100 hover:bg-zinc-200">
                <IconArrowLeft className="h-5 w-5 stroke-zinc-500" />
              </div>
              <div className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-zinc-100 hover:bg-zinc-200">
                <IconArrowRight className="h-5 w-5 stroke-zinc-500" />
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="flex w-full flex-col overflow-x-auto bg-gradient-to-r from-white to-zinc-100 px-6 py-5 md:items-center">
        <div className="grid w-[720px] grid-flow-col justify-between">
          {topFiveCategoryInds.map((catInd, i) => (
            <Card
              key={i}
              category={ceremony.categories[catInd]}
              imageUrl={topFiveImageUrls[i]}
            />
          ))}
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
                <div className="sticky top-0 z-30 flex h-14 flex-row items-center justify-between bg-white text-sm font-medium text-zinc-500">
                  <div className="flex flex-row gap-4">
                    <div>All</div>
                    <div>Category: All</div>
                  </div>
                  <div className="font-semibold">
                    {ceremony.official_year} ({ordinal})
                  </div>
                </div>
                <hr />
                {ceremony.categories.map((c, i) => (
                  <Category key={i} categoryInfo={c} />
                ))}
              </TabPanel>
              <TabPanel>
                <Stats stats={nominations.stats} />
              </TabPanel>
            </TabPanels>
          </TabGroup>
        </div>
      </section>
    </div>
  );
}

function Card({
  category,
  imageUrl,
}: {
  category: CategoryType;
  imageUrl: string;
}) {
  const personFirst =
    category.nominees[0].is_person || category.short_name === "Director";
  return (
    <div className="flex w-[135px] flex-col gap-2">
      <a
        className="w-fit max-w-full cursor-pointer truncate text-xxs font-semibold text-zinc-800 hover:text-gold"
        title={
          category.short_name.startsWith("Unique")
            ? category.short_name
            : "Best " + category.short_name
        }
      >
        {(category.short_name.startsWith("Unique")
          ? category.short_name
          : "Best " + category.short_name
        ).toUpperCase()}
      </a>
      <div className="relative h-[200px] overflow-hidden rounded-[0.25rem] border border-zinc-300 bg-zinc-50">
        <Image
          src={imageUrl}
          fill={true}
          alt={
            personFirst
              ? `Photo of ${category.nominees[0].people[0].name}`
              : `Cover of ${category.nominees[0].titles[0].title}`
          }
          priority={true}
          className="object-cover"
        />
      </div>
      <div className="flex flex-col gap-1 font-medium text-zinc-800">
        <div className="text-sm leading-4 text-zinc-800">
          {!personFirst ? (
            <a className="cursor-pointer italic underline decoration-zinc-200 underline-offset-2 hover:text-gold">
              {category.nominees[0].titles[0].title}
            </a>
          ) : (
            category.nominees[0].people.map((n, i) => (
              <span key={i}>
                <a className="cursor-pointer underline decoration-zinc-200 underline-offset-2 hover:text-gold">
                  {n.name}
                </a>
                {i != category.nominees[0].people.length - 1 && ", "}
              </span>
            ))
          )}
        </div>
        <div className="text-xs leading-[0.875rem] text-zinc-500">
          {!personFirst ? (
            category.nominees[0].people.map((n, i) => (
              <span key={i}>
                <a className="cursor-pointer underline decoration-zinc-200 underline-offset-2 hover:text-gold">
                  {n.name}
                </a>
                {i != category.nominees[0].people.length - 1 && ", "}
              </span>
            ))
          ) : (
            <a className="cursor-pointer italic underline decoration-zinc-200 underline-offset-2 hover:text-gold">
              {category.nominees[0].titles[0].title}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function Nominee({
  category,
  nomineeInfo,
}: {
  category: string;
  nomineeInfo: NomineeType;
}) {
  return (
    <div className="flex flex-row gap-2.5">
      <IconStarFilled
        className={`${nomineeInfo.winner ? "visible" : "invisible"} mt-[3px] h-4 w-4 flex-shrink-0 fill-gold`}
      />
      <div
        className={`${nomineeInfo.is_person || nomineeInfo.titles.length == 0 ? "flex-col" : "flex-col-reverse"} flex gap-1`}
      >
        <div
          className={`${nomineeInfo.is_person || nomineeInfo.titles.length == 0 ? "text-base font-medium leading-5 text-zinc-800" : "text-sm font-normal leading-4 text-zinc-500"}`}
        >
          {nomineeInfo.people.map((p, i) => (
            <span key={i}>
              <Link
                href={`/entity/${p.id}`}
                className="w-fit cursor-pointer underline decoration-zinc-300 underline-offset-2 hover:text-gold"
              >
                {p.name}
              </Link>
              {i != nomineeInfo.people.length - 1 && ", "}
            </span>
          ))}
          {(nomineeInfo.is_person || nomineeInfo.titles.length == 0) &&
            nomineeInfo.note && <Note text={nomineeInfo.note} />}
        </div>
        <div
          className={`${!nomineeInfo.is_person || nomineeInfo.titles.length == 0 ? "text-base font-medium leading-5 text-zinc-800" : "text-sm font-normal leading-4 text-zinc-500"}`}
        >
          {nomineeInfo.titles.map((t, i) => {
            return (
              <span key={i}>
                {t.detail.map((d, j) => (
                  <span key={j}>
                    <span className="w-fit">
                      {category == "Original Song" ||
                      category == "Dance Direction"
                        ? "“" + d + "”"
                        : d}
                    </span>
                    {", "}
                  </span>
                ))}
                <span>
                  <Link
                    href={`/title/${t.id}`}
                    className="w-fit cursor-pointer italic underline decoration-zinc-300 underline-offset-2 hover:text-gold"
                  >
                    {t.title}
                  </Link>
                  {i != nomineeInfo.titles.length - 1 && (
                    <span className="select-none">&nbsp;&thinsp;·&nbsp;</span>
                  )}
                </span>
              </span>
            );
          })}
          {!nomineeInfo.is_person &&
            nomineeInfo.titles.length != 0 &&
            nomineeInfo.note && <Note text={nomineeInfo.note} />}
        </div>
      </div>
    </div>
  );
}

function Note({ text }: { text: string }) {
  return (
    <span className="select-none">
      &nbsp;
      <span
        className="group relative z-0 cursor-pointer align-top text-xs font-medium text-gold"
        title={text}
      >
        <span className="z-0 group-hover:underline">N</span>
      </span>
    </span>
  );
}

function Category({ categoryInfo }: { categoryInfo: CategoryType }) {
  return (
    <>
      <div className="flex flex-col gap-1 py-6 text-zinc-800 sm:flex-row sm:gap-6">
        <div className="sticky top-14 z-20 flex-1 bg-white pb-4">
          <h1 className="sticky top-14 flex w-fit cursor-pointer text-xl font-medium leading-6 hover:text-gold sm:text-lg sm:leading-6">
            {categoryInfo.common_name}
          </h1>
        </div>
        <div className="flex flex-1 flex-col gap-[0.875rem]">
          {categoryInfo.nominees.map((n, i) => (
            <Nominee
              key={i}
              category={categoryInfo.short_name}
              nomineeInfo={n}
            />
          ))}
        </div>
      </div>
      <hr />
    </>
  );
}
