import AwardNavigator from "@/app/_components/awardNavigator";
import Breadcrumbs from "@/app/_components/breadcrumbs";
import type { SmallSelectorOption } from "@/app/_components/selectors";
import fetchError from "@/app/_utils/fetchError";
import merge from "@/app/_utils/merge";
import { dateToString, iterationToOrdinal } from "@/app/_utils/utils";
import { IconArrowLeft, IconArrowRight } from "@tabler/icons-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { AwardEnum, type EditionType } from "./types";

export default async function CeremonyLayout({
  params,
  children,
}: {
  params: Promise<{ iteration: string }>;
  children: React.ReactNode;
}) {
  const iteration = parseInt((await params).iteration);
  if (Number.isNaN(iteration)) {
    notFound();
  }

  const ordinal = iterationToOrdinal(iteration);
  const editions: EditionType[] = await fetchError("/api/ceremonies");
  const currentEditionInd = editions.findIndex(
    (e) => e.iteration === iteration,
  );
  const currentEdition = editions[currentEditionInd];

  const awardNavigatorOptions: SmallSelectorOption[] = editions.map((e) => ({
    id: e.iteration,
    name: e.official_year + " (" + iterationToOrdinal(e.iteration) + ")",
    disabled: false,
  }));
  const originalAwardNavigatorOption: SmallSelectorOption =
    awardNavigatorOptions[currentEditionInd];

  const disableNextLink = iteration === editions.length;
  const disablePrevLink = iteration === 1;

  return (
    <div className="flex flex-col gap-5">
      <nav className="mx-auto flex w-full flex-row justify-between px-6 pt-5 text-xs md:w-[768px]">
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
      <div className="mx-auto flex w-full flex-row items-center justify-between px-6 md:w-[768px]">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-medium leading-7 text-zinc-800">
            {ordinal} Academy Awards
          </h1>
          <h2 className="text-sm font-medium leading-4 text-zinc-500">
            <span>{dateToString(currentEdition.ceremony_date)}</span>
            <span className="select-none">&#32;·&#32;</span>
            <span>Honoring films from {currentEdition.official_year}</span>
          </h2>
        </div>
        <div className="hidden flex-row gap-2 sm:flex">
          <Link
            href={`/ceremony/${currentEdition.iteration - 1}`}
            tabIndex={disablePrevLink ? -1 : 0}
            aria-disabled={disablePrevLink}
            className={merge(
              disablePrevLink
                ? "bg-overlay-disabled pointer-events-none opacity-50"
                : "cursor-pointer hover:bg-zinc-200",
              "flex size-8 items-center justify-center rounded-full bg-overlay",
            )}
          >
            <IconArrowLeft className="size-5 stroke-secondary" />
          </Link>
          <Link
            href={`/ceremony/${currentEdition.iteration + 1}`}
            tabIndex={disableNextLink ? -1 : 0}
            aria-disabled={disableNextLink}
            className={merge(
              disableNextLink
                ? "bg-overlay-disabled pointer-events-none opacity-50"
                : "cursor-pointer hover:bg-zinc-200",
              "flex size-8 items-center justify-center rounded-full bg-overlay",
            )}
          >
            <IconArrowRight className="size-5 stroke-secondary" />
          </Link>
        </div>
      </div>
      {children}
    </div>
  );
}
