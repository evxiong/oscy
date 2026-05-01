import AwardNavigator from "@/app/_components/AwardNavigator";
import Breadcrumbs from "@/app/_components/Breadcrumbs";
import type { SmallSelectorOption } from "@/app/_components/Selectors";
import { fetchApi } from "@/app/_utils/fetch";
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
  const editions: EditionType[] = await fetchApi("/ceremonies");
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
          <h1 className="text-2xl/7 font-medium text-primary">
            {ordinal} Academy Awards
          </h1>
          <h2 className="text-sm/4 font-medium text-secondary">
            <span>{dateToString(currentEdition.ceremony_date)}</span>
            <span className="select-none">&#32;·&#32;</span>
            <span>Honoring films from {currentEdition.official_year}</span>
          </h2>
        </div>
        <div className="hidden flex-row gap-2 sm:flex">
          <Link
            aria-label="Previous ceremony"
            href={`/ceremony/${disablePrevLink ? currentEdition.iteration : currentEdition.iteration - 1}`}
            tabIndex={disablePrevLink ? -1 : 0}
            aria-disabled={disablePrevLink}
            className={merge(
              disablePrevLink
                ? "bg-overlay-disabled pointer-events-none opacity-50"
                : "cursor-pointer hover:bg-active",
              "flex size-8 items-center justify-center rounded-full bg-overlay",
            )}
          >
            <IconArrowLeft aria-hidden className="size-5 stroke-secondary" />
          </Link>
          <Link
            aria-label="Next ceremony"
            href={`/ceremony/${disableNextLink ? currentEdition.iteration : currentEdition.iteration + 1}`}
            tabIndex={disableNextLink ? -1 : 0}
            aria-disabled={disableNextLink}
            className={merge(
              disableNextLink
                ? "bg-overlay-disabled pointer-events-none opacity-50"
                : "cursor-pointer hover:bg-active",
              "flex size-8 items-center justify-center rounded-full bg-overlay",
            )}
          >
            <IconArrowRight aria-hidden className="size-5 stroke-secondary" />
          </Link>
        </div>
      </div>
      {children}
    </div>
  );
}
