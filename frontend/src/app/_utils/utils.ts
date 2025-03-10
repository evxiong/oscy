import { CategoryName } from "../category/[id]/types";
import { CategoryType, NominationsType } from "../ceremony/[iteration]/types";
import fetchRetryWrapper from "fetch-retry";

interface TopFive {
  indices: number[];
  imdb_ids: string[];
}

interface TimelineItem {
  start_year: number;
  start_iteration: number;
  end_year: number;
  end_iteration: number;
  name: string;
}

interface TMDBResults {
  movie_results: {
    poster_path: string;
  }[];
  person_results: {
    profile_path: string;
  }[];
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

export function ceremonyToTopFive(
  nominations: NominationsType,
): TopFive | null {
  // returns list of five category indices in ceremony, and the winner imdb ids to be used in cards
  const ceremony = nominations.editions[0];

  if (ceremony.categories[0].nominees[0].pending) {
    return null;
  }

  const indices = new Array<number>(5);
  const imdb_ids = new Array<string>(5);

  const writingCategories = new Set([
    "Adapted Screenplay",
    "Original Screenplay",
    "Screenplay",
    "Story",
  ]);

  const categoryToIndex = new Map([
    ["Picture", 0],
    ["Director", 1],
    ["Unique and Artistic Picture", 1],
    ["Actor", 2],
    ["Actress", 3],
  ]);

  const titleIdToCategoryIndex = new Map();

  // rankings: picture, director or unique picture, actor, actress, writing w/ most wins
  for (let i = 0; i < ceremony.categories.length; i++) {
    const ind = categoryToIndex.get(ceremony.categories[i].short_name);
    if (ind !== undefined) {
      indices[ind] = i;
      if (
        ceremony.categories[i].nominees[0].is_person ||
        ceremony.categories[i].short_name === "Director"
      ) {
        imdb_ids[ind] = ceremony.categories[i].nominees[0].people[0].imdb_id;
      } else {
        imdb_ids[ind] = ceremony.categories[i].nominees[0].titles[0].imdb_id;
      }
    }

    if (writingCategories.has(ceremony.categories[i].short_name)) {
      // note the category index and winner title id
      const winnerTitleId = ceremony.categories[i].nominees[0].titles?.[0].id;
      titleIdToCategoryIndex.set(winnerTitleId, i);
    }
  }

  // iterate thru titles sorted by wins desc until matching winner title id found
  const sortedTitleStats = [...nominations.stats.title_stats].sort(
    (a, b) => b.wins - a.wins || b.noms - a.noms,
  );
  for (const t of sortedTitleStats) {
    const ind = titleIdToCategoryIndex.get(t.id);
    if (ind !== undefined) {
      indices[4] = ind;
      imdb_ids[4] = t.imdb_id;
      break;
    }
  }

  const topFive: TopFive = {
    indices: indices,
    imdb_ids: imdb_ids,
  };

  return topFive;
}

export function categoriesToTopFive(categories: CategoryType[]): TopFive {
  // categories should already be reversed
  const indices = [];
  const imdb_ids = [];

  let i = 0;
  for (const c of categories) {
    if (c.nominees[0].pending) {
      i += 1;
      continue;
    }
    if (c.nominees[0].is_person || c.short_name === "Director") {
      imdb_ids.push(
        c.nominees[0].people[0]?.imdb_id ?? c.nominees[0].titles[0].imdb_id,
      );
    } else {
      imdb_ids.push(
        c.nominees[0].titles[0]?.imdb_id ?? c.nominees[0].people[0].imdb_id,
      );
    }
    indices.push(i);
    if (imdb_ids.length === 5) {
      break;
    }
    i += 1;
  }

  const topFive: TopFive = {
    indices: indices,
    imdb_ids: imdb_ids,
  };

  return topFive;
}

export async function topFiveToImageUrls(
  topFive: TopFive,
): Promise<(string | null)[]> {
  const fetchRetry = fetchRetryWrapper(fetch);
  return Promise.all(
    process.env.TMDB_API_KEY
      ? topFive.imdb_ids.map(async (imdb_id) => {
          const findByIdResults = await fetchRetry(
            `https://api.themoviedb.org/3/find/${imdb_id}?external_source=imdb_id&api_key=${process.env.TMDB_API_KEY}`,
            {
              retryOn: (attempt, error, response) => {
                if (attempt < 3 && (!response || !response.ok)) {
                  console.log(
                    `Retrying after ${error?.message}: attempt ${attempt + 1}`,
                  );
                  return true;
                }
                return false;
              },
              retryDelay: 5000,
            },
          );
          if (!findByIdResults.ok) {
            throw new Error(
              `Failed to connect to TMDB API: check validity of TMDB_API_KEY in .env: ${process.env.TMDB_API_KEY}`,
            );
          }
          const results: TMDBResults = await findByIdResults.json();
          if (imdb_id.startsWith("tt")) {
            return results["movie_results"].length > 0 &&
              results["movie_results"][0]["poster_path"]
              ? "https://image.tmdb.org/t/p/w185" +
                  results["movie_results"][0]["poster_path"]
              : null;
          } else {
            return results["person_results"].length > 0 &&
              results["person_results"][0]["profile_path"]
              ? "https://image.tmdb.org/t/p/w185" +
                  results["person_results"][0]["profile_path"]
              : null;
          }
        })
      : [null, null, null, null, null],
  );
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
