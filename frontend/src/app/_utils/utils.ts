import { unstable_cache } from "next/cache";
import type { QuickLink } from "../_components/SearchBar";
import { CategoryName, type CategoryGroupInfo } from "../category/[id]/types";
import { NominationsType } from "../ceremony/[iteration]/types";
import { fetchApi, fetchImageUrl, fetchVersion } from "./fetch";

export interface TimelineItem {
  start_year: number;
  start_iteration: number;
  end_year: number;
  end_iteration: number;
  name: string;
}

export interface ImageInfo {
  src: string;
  alt: string;
}

export function dateToString(date: string): string {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });
}

export function iterationToOrdinal(iteration: number): string {
  const suffixes = ["th", "st", "nd", "rd"];
  const v = iteration % 100;
  return iteration + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
}

export function categoryNamesToTimeline(
  categoryNames: CategoryName[],
): TimelineItem[] {
  // create one entry per discrete range/name combination
  // sort desc by end of range (gtd no ties)
  const items = categoryNames
    .map((cn) =>
      cn.ranges.map((r) => ({
        start_year: 1927 + r[0],
        start_iteration: r[0],
        end_year: 1927 + r[1],
        end_iteration: r[1],
        name: cn.common_name,
      })),
    )
    .flat()
    .sort((a, b) => b.end_iteration - a.end_iteration);

  return items;
}

export function imdbIdToUrl(imdbId: string): string {
  if (imdbId.startsWith("nm")) {
    return "https://www.imdb.com/name/" + imdbId;
  } else if (imdbId.startsWith("tt")) {
    return "https://www.imdb.com/title/" + imdbId;
  } else if (imdbId.startsWith("co")) {
    return "https://www.imdb.com/search/title/?companies=" + imdbId;
  } else {
    throw new Error(`Invalid IMDb id: ${imdbId}`);
  }
}

export const getBestPictureImages = unstable_cache(
  async () => {
    try {
      const currentVersion = await fetchVersion();
      const currentEdition: NominationsType = await fetchApi(
        `/ceremonies/${currentVersion.iteration}`,
      );
      const category = currentEdition.editions[0].categories.find(
        (c) => c.short_name === "Picture",
      )!;
      const imdbIds = category.nominees.map((n) => n.titles[0].imdb_id);
      const titles = category.nominees.map((n) => n.titles[0].title);

      if (!process.env.TMDB_API_KEY) {
        return null;
      }

      // fetch tmdb posters for these ids
      const imageUrls = await Promise.all(
        imdbIds.map((imdbId) => fetchImageUrl(imdbId, true)),
      );

      const images: ImageInfo[] = imageUrls.map((imageUrl, i) => ({
        src: imageUrl as string,
        alt: `Poster for ${titles[i]}`,
      }));
      return images;
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error(error.message);
      } else {
        console.error(error);
      }
      return null;
    }
  },
  undefined,
  {
    revalidate: false,
    tags: ["version"],
  },
);

export const getQuickLinks = unstable_cache(
  async (categories: string[]) => {
    try {
      const currentVersion = await fetchVersion();
      const currentEdition = currentVersion.iteration;

      const categoryGroups: CategoryGroupInfo[] = await fetchApi("/categories");
      const categoryToId = new Map<string, number>(
        categoryGroups.flatMap((cg) =>
          cg.categories.map((c) => [c.category, c.category_id]),
        ),
      );

      const quickLinks: QuickLink[] = [
        {
          name: `${1927 + currentEdition} (${iterationToOrdinal(currentEdition)}) Academy Awards`,
          url: `/ceremony/${currentEdition}`,
          type: "ceremony",
        },
      ];

      for (const c of categories) {
        if (categoryToId.has(c)) {
          quickLinks.push({
            name: `Best ${c}`,
            url: `/category/${categoryToId.get(c)!}`,
            type: "category",
          });
        }
      }

      return quickLinks;
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error(error.message);
      } else {
        console.error(error);
      }
      return [];
    }
  },
  undefined,
  {
    revalidate: false,
    tags: ["version"],
  },
);
