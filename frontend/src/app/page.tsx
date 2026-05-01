import {
  IconAdjustments,
  IconBlendMode,
  IconBrandGithub,
  IconLaurelWreath,
  IconSparkles,
  IconTableHeart,
} from "@tabler/icons-react";
import { Metadata } from "next";
import { Carousel } from "./_components/Carousel";
import ExploreButton from "./_components/ExploreButton";
import ExternalLink from "./_components/ExternalLink";
import PrefetchLink from "./_components/PrefetchLink";
import { buttonVariants } from "./_ui/variants";
import { fetchVersion } from "./_utils/fetch";
import { getBestPictureImages, iterationToOrdinal } from "./_utils/utils";

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

export default async function Home() {
  const currentVersion = await fetchVersion();
  const currentEdition = currentVersion.iteration;
  const currentYear = 1927 + currentEdition;
  const currentOrdinal = iterationToOrdinal(currentEdition);
  const updateDate = new Date(currentVersion.updated_at);
  const updateMonth = updateDate.toLocaleDateString("en-US", { month: "long" });

  const bestPictureImages = await getBestPictureImages();
  return (
    <div className="flex flex-col">
      <section className="flex w-full flex-col items-center bg-gradient-to-b from-background to-light pb-12 pt-10">
        <div className="w-full md:w-[768px]">
          <div className="flex flex-col items-center gap-6 px-6">
            <div className="w-fit rounded-full text-sm font-medium text-secondary">
              <span>{updateMonth} update:</span>&ensp;
              <PrefetchLink
                href={`/ceremony/${currentEdition}`}
                className="group/link cursor-pointer"
              >
                <IconLaurelWreath
                  aria-hidden
                  className="inline-flex size-4 shrink-0 stroke-tertiary"
                />
                &nbsp;
                <span className="underline decoration-border underline-offset-4 group-hover/link:decoration-secondary">
                  {`${currentOrdinal} Academy Awards`}
                </span>
              </PrefetchLink>
            </div>
            <div>
              <h1 className="text-balance text-center text-4xl font-medium tracking-tight text-title">
                An{" "}
                <span className="underline decoration-border decoration-2 underline-offset-[6px]">
                  open-source
                </span>{" "}
                Oscars database and API, designed for querying nomination stats.
              </h1>
            </div>

            <div className="mt-2 flex flex-row gap-4">
              <ExternalLink
                href="https://github.com/evxiong/oscy"
                className={buttonVariants({ variant: "primary" })}
              >
                <IconBrandGithub aria-hidden />
                <span className="hidden xs:block">View on GitHub</span>
                <span className="xs:hidden">GitHub</span>
              </ExternalLink>
              <ExploreButton id="explore-home">
                <span className="hidden xs:block">Explore database</span>
                <span className="xs:hidden">Explore</span>
              </ExploreButton>
            </div>
          </div>
          {bestPictureImages && (
            <>
              <div className="mt-4 h-64 w-full">
                <Carousel
                  images={[...bestPictureImages, ...bestPictureImages]}
                />
              </div>
              <div className="flex w-full flex-col items-center justify-center text-xxs font-semibold uppercase text-tertiary">
                <p>{`${currentYear} (${currentOrdinal}) Academy Awards`}</p>
                <p>Best Picture &mdash; Nominees</p>
              </div>
            </>
          )}
        </div>
      </section>
      <section className="mb-10 flex w-full flex-col items-center gap-8 pb-8 pt-8">
        <div className="px-6 md:w-[768px]">
          <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2">
            <Card>
              <IconTableHeart aria-hidden className="stroke-subtitle" />
              <CardTitle>Curated data</CardTitle>
              <CardDescription>
                Database records have been painstakingly reviewed for accuracy.
              </CardDescription>
            </Card>
            <Card>
              <IconBlendMode aria-hidden className="stroke-subtitle" />
              <CardTitle>Nominees matched to IMDb IDs</CardTitle>
              <CardDescription>
                Extend oscy as you see fit, including with{" "}
                <ExternalLink
                  href="https://developer.themoviedb.org/reference/find-by-id"
                  className="underline decoration-underline decoration-1 underline-offset-[3px] hover:decoration-current"
                >
                  TMDB
                </ExternalLink>
                .
              </CardDescription>
            </Card>
            <Card>
              <IconAdjustments aria-hidden className="stroke-subtitle" />
              <CardTitle>Powered by PostgreSQL</CardTitle>
              <CardDescription>
                Discover superlatives, streaks, and more with advanced queries.
              </CardDescription>
            </Card>
            <Card>
              <IconSparkles aria-hidden className="stroke-subtitle" />
              <CardTitle>No SQL, no problem</CardTitle>
              <CardDescription>
                <ExternalLink
                  href="/api/docs"
                  className="underline decoration-underline decoration-1 underline-offset-[3px] hover:decoration-current"
                >
                  User-friendly API
                </ExternalLink>{" "}
                handles most common queries.
              </CardDescription>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col rounded-md border border-overlay bg-gradient-to-b from-background to-light p-4 shadow-sm">
      {children}
    </div>
  );
}

function CardTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mt-2 text-xl font-medium tracking-tight text-subtitle">
      {children}
    </h2>
  );
}

function CardDescription({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-1 text-base/5 font-medium tracking-tight text-secondary">
      {children}
    </p>
  );
}
