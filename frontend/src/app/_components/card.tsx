import Link from "next/link";
import { CategoryType } from "../ceremony/[iteration]/types";
import Image from "next/image";
import { IconLibraryPhoto } from "@tabler/icons-react";

export default function Card({
  showCeremony,
  ceremony,
  ceremonyId,
  category,
  imageUrl,
}: {
  showCeremony: boolean;
  ceremony: string;
  ceremonyId: number;
  category: CategoryType;
  imageUrl: string | null;
}) {
  const personFirst =
    category.nominees[0].is_person ||
    category.short_name === "Director" ||
    category.nominees[0].titles.length === 0;
  const detailsFirst =
    category.short_name === "Original Song" ||
    category.short_name === "Dance Direction";
  const titleWinners = category.nominees[0].titles.filter(
    (t) => t.title_winner,
  );
  return (
    <div className="flex w-[135px] flex-shrink-0 flex-col gap-2">
      <Link
        prefetch={false}
        href={
          showCeremony
            ? `/ceremony/${ceremonyId}`
            : `/category/${category.category_id}`
        }
        className="w-fit max-w-full cursor-pointer truncate text-xxs font-semibold text-zinc-800 hover:text-gold"
        title={
          showCeremony
            ? ceremony
            : category.short_name.startsWith("Unique")
              ? category.short_name
              : "Best " + category.short_name
        }
      >
        {(showCeremony
          ? ceremony
          : category.short_name.startsWith("Unique")
            ? category.short_name
            : "Best " + category.short_name
        ).toUpperCase()}
      </Link>
      <div className="relative h-[200px] overflow-hidden rounded-[0.25rem] border border-zinc-300 bg-transparent">
        {imageUrl ? (
          <Image
            src={imageUrl}
            draggable={false}
            fill={true}
            alt={
              personFirst
                ? `Photo of ${category.nominees[0].people[0]?.name ?? category.nominees[0].titles[0].title}`
                : `Poster for ${category.nominees[0].titles[0]?.title ?? category.nominees[0].people[0].name}`
            }
            priority={true}
            className="object-cover"
          />
        ) : (
          <div className="flex h-full w-full select-none items-center justify-center text-zinc-300">
            <div className="flex flex-col items-center gap-2">
              <IconLibraryPhoto />
              <div className="text-center text-sm font-semibold leading-4">
                NO IMAGE AVAILABLE
              </div>
            </div>
          </div>
        )}
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
                prefetch={false}
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
          {detailsFirst
            ? category.nominees[0].titles[0].detail.map((d, i) => (
                <span key={i}>
                  <span className="w-fit">{"“" + d + "”"}</span>
                  {i < category.nominees[0].titles[0].detail.length - 1 && ", "}
                </span>
              ))
            : titleWinners.map((t, i) => (
                <span key={i}>
                  <Link
                    prefetch={false}
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
