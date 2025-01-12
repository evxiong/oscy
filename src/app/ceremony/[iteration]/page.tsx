import { TabGroup, TabList, Tab, TabPanels, TabPanel } from "@headlessui/react";
import { IconArrowLeft, IconArrowRight } from "@tabler/icons-react";
import { ceremonyToTopFive, iterationToOrdinal } from "@/app/_utils/utils";
import { AwardType, CategoryType, EditionType, NominationsType } from "./types";
import Image from "next/image";
import Link from "next/link";
import Stats from "./stats";
import Nominations from "./nominations";
import Breadcrumbs from "@/app/_components/breadcrumbs";
import CeremonySelector from "./ceremonySelector";

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
          <nav className="flex flex-row justify-between text-xs">
            <Breadcrumbs
              crumbs={[
                { name: "Home", link: "/" },
                { name: "Ceremony", link: "" },
              ]}
            />
            <CeremonySelector
              awardType={AwardType.oscar}
              editions={editions}
              currentId={ceremony.id}
            />
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
                <Nominations
                  categories={ceremony.categories}
                  officialYear={ceremony.official_year}
                  ordinal={ordinal}
                />
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
  const titleWinners = category.nominees[0].titles.filter(
    (t) => t.title_winner,
  );
  return (
    <div className="flex w-[135px] flex-col gap-2">
      <Link
        href={`/category/${category.category_id}`}
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
      </Link>
      <div className="relative h-[200px] overflow-hidden rounded-[0.25rem] border border-zinc-300 bg-zinc-50">
        <Image
          src={imageUrl}
          fill={true}
          alt={
            personFirst
              ? `Photo of ${category.nominees[0].people[0].name}`
              : `Poster for ${category.nominees[0].titles[0].title}`
          }
          priority={true}
          className="object-cover"
        />
      </div>
      <div
        className={`${personFirst ? "flex-col" : "flex-col-reverse"} flex gap-1`}
      >
        <div
          className={`${personFirst ? "text-sm font-medium leading-4 text-zinc-800" : "text-xs font-normal leading-[0.875rem] text-zinc-500"} `}
        >
          {category.nominees[0].people.map((n, i) => (
            <span key={i}>
              <Link
                href={`/entity/${n.id}`}
                className="w-fit cursor-pointer underline decoration-zinc-200 underline-offset-2 hover:text-gold"
              >
                {n.name}
              </Link>
              {i !== category.nominees[0].people.length - 1 && ", "}
            </span>
          ))}
        </div>
        <div
          className={`${!personFirst ? "text-sm font-medium leading-4 text-zinc-800" : "text-xs leading-[0.875rem] text-zinc-500"} `}
        >
          {titleWinners.map((t, i) => (
            <span key={i}>
              <Link
                href={`/title/${t.id}`}
                className="w-fit cursor-pointer italic underline decoration-zinc-200 underline-offset-2 hover:text-gold"
              >
                {t.title}
              </Link>
              {i !== titleWinners.length - 1 && (
                <span className="select-none">&nbsp;&thinsp;·&nbsp;</span>
              )}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
