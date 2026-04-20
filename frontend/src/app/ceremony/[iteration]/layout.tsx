import AwardNavigator from "@/app/_components/awardNavigator";
import Breadcrumbs from "@/app/_components/breadcrumbs";
import type { SmallSelectorOption } from "@/app/_components/selectors";
import fetchError from "@/app/_utils/fetchError";
import { iterationToOrdinal } from "@/app/_utils/utils";
import { AwardEnum, type EditionType } from "./types";

export default async function CeremonyLayout({
  params,
  children,
}: {
  params: Promise<{ iteration: string }>;
  children: React.ReactNode;
}) {
  const iteration = parseInt((await params).iteration);
  const editions: EditionType[] = await fetchError("/api/ceremonies");
  const awardNavigatorOptions: SmallSelectorOption[] = editions.map((e) => ({
    id: e.iteration,
    name: e.official_year + " (" + iterationToOrdinal(e.iteration) + ")",
    disabled: false,
  }));
  const originalAwardNavigatorOption: SmallSelectorOption =
    awardNavigatorOptions[editions.findIndex((e) => e.iteration === iteration)];

  return (
    <>
      <nav className="mx-auto flex flex-row justify-between px-6 py-5 text-xs md:w-[768px]">
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
      {children}
    </>
  );
}
