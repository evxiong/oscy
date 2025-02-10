import { Metadata } from "next";
import ExploreButton from "./_components/exploreButton";
import {
  IconAdjustments,
  IconBlendMode,
  IconBrandGithub,
  IconSparkles,
  IconTableHeart,
} from "@tabler/icons-react";

const title = "oscy - Open-source Oscars database and API";
const description = "Use oscy in your next movie-related project.";

export const metadata: Metadata = {
  title: title,
  description: description,
  openGraph: {
    siteName: "oscy",
    title: title,
    description: description,
    type: "website",
    url: "/",
  },
  twitter: {
    card: "summary",
    title: title,
    description: description,
  },
};

export default function Home() {
  return (
    <div className="flex flex-col">
      <section className="flex w-full flex-col items-center bg-gradient-to-b from-white to-zinc-50 pb-16 pt-10">
        <div className="flex w-full flex-col items-center gap-8 px-6 md:w-[768px]">
          <div className="flex flex-row justify-between text-sm font-medium text-zinc-500">
            - pronounced OS-kee -
          </div>
          <div>
            <h1 className="text-center text-4xl font-medium tracking-tight text-zinc-600">
              An{" "}
              <span className="underline decoration-zinc-200 underline-offset-[6px]">
                open-source
              </span>{" "}
              Oscars* database and API, designed for querying nomination stats
            </h1>
            <h3 className="mt-4 text-center text-xl font-normal leading-6 tracking-tight text-zinc-500">
              * with Emmy nominations coming soon
            </h3>
          </div>

          <div className="xs:flex xs:flex-row xs:gap-4 hidden">
            <a
              target="_blank"
              rel="noopener noreferrer"
              href="https://github.com/evxiong/oscy"
              className="flex cursor-pointer flex-row items-center gap-2 rounded-md border border-zinc-400 px-4 py-2 text-sm font-medium text-zinc-500 hover:border-zinc-800 hover:text-zinc-800 focus:border-zinc-800 focus:text-zinc-800 focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
            >
              <IconBrandGithub className="size-4" />
              <span>View on GitHub</span>
            </a>
            <ExploreButton id="explore-1" text="Explore database" />
          </div>
          <div className="xs:hidden flex flex-row gap-4">
            <a
              target="_blank"
              rel="noopener noreferrer"
              href="https://github.com/evxiong/oscy"
              className="flex cursor-pointer flex-row items-center gap-2 rounded-md border border-zinc-400 px-4 py-2 text-sm font-medium text-zinc-500 hover:border-zinc-800 hover:text-zinc-800 focus:border-zinc-800 focus:text-zinc-800 focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
            >
              <IconBrandGithub className="size-4" />
              <span>GitHub</span>
            </a>
            <ExploreButton id="explore-2" text="Explore" />
          </div>
        </div>
      </section>
      <section className="mb-10 flex w-full flex-col items-center gap-8 py-16">
        <div className="grid w-full grid-cols-1 gap-4 px-6 sm:grid-cols-2 md:w-[768px]">
          <div className="flex flex-col rounded-md border p-4">
            <IconTableHeart className="stroke-zinc-600" />
            <h2 className="mt-2 text-xl font-medium tracking-tight text-zinc-600">
              Curated data
            </h2>
            <h3 className="mt-1 text-base font-medium leading-5 tracking-tight text-zinc-500">
              Database records have been painstakingly reviewed for accuracy.
            </h3>
          </div>
          <div className="flex flex-col rounded-md border p-4">
            <IconBlendMode className="stroke-zinc-600" />
            <h2 className="mt-2 text-xl font-medium tracking-tight text-zinc-600">
              Nominees matched to IMDb IDs
            </h2>
            <h3 className="mt-1 text-base font-medium leading-5 tracking-tight text-zinc-500">
              Extend <span className="">oscy</span> as you see fit, including
              with{" "}
              <a
                target="_blank"
                rel="noopener noreferrer"
                href="https://developer.themoviedb.org/reference/find-by-id"
                className="underline decoration-zinc-300 underline-offset-4 hover:decoration-zinc-500"
              >
                TMDB
              </a>
              .
            </h3>
          </div>
          <div className="flex flex-col rounded-md border p-4">
            <IconSparkles className="stroke-zinc-600" />
            <h2 className="mt-2 text-xl font-medium tracking-tight text-zinc-600">
              No SQL, no problem
            </h2>
            <h3 className="mt-1 text-base font-medium leading-5 tracking-tight text-zinc-500">
              User-friendly API handles most common queries.
            </h3>
          </div>
          <div className="flex flex-col rounded-md border p-4">
            <IconAdjustments className="stroke-zinc-600" />
            <h2 className="mt-2 text-xl font-medium tracking-tight text-zinc-600">
              Postgres for advanced queries
            </h2>
            <h3 className="mt-1 text-base font-medium leading-5 tracking-tight text-zinc-500">
              Sort/filter nominations by edition, category, and more.
            </h3>
          </div>
        </div>
      </section>
    </div>
  );
}
