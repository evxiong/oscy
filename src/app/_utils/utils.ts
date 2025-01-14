import { CategoryName } from "../category/[id]/types";
import { CategoryType, NominationsType } from "../ceremony/[iteration]/types";

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

export function iterationToOrdinal(iteration: number): string {
  const suffixes = ["th", "st", "nd", "rd"];
  const v = iteration % 100;
  return iteration + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
}

export function ceremonyToTopFive(nominations: NominationsType): TopFive {
  // returns list of five category indices in ceremony, and the winner imdb ids to be used in cards
  const ceremony = nominations.editions[0];

  var indices = new Array<number>(5);
  var imdb_ids = new Array<string>(5);

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

  let titleIdToCategoryIndex = new Map();

  // rankings: picture, director or unique picture, actor, actress, writing w/ most noms
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

  // iterate thru titles sorted by noms desc until matching winner title id found
  for (const t of nominations.stats.title_stats) {
    const ind = titleIdToCategoryIndex.get(t.id);
    if (ind !== undefined) {
      indices[4] = ind;
      imdb_ids[4] = t.imdb_id;
      break;
    }
  }

  let topFive: TopFive = {
    indices: indices,
    imdb_ids: imdb_ids,
  };

  return topFive;
}

export function categoriesToTopFive(categories: CategoryType[]): TopFive {
  // categories should already be reversed
  var indices = [];
  var imdb_ids = [];

  let i = 0;
  for (const c of categories) {
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

  let topFive: TopFive = {
    indices: indices,
    imdb_ids: imdb_ids,
  };

  return topFive;
}

export async function topFiveToImageUrls(
  topFive: TopFive,
): Promise<(string | null)[]> {
  return Promise.all(
    topFive.imdb_ids.map(async (imdb_id) => {
      let res = await fetch(
        `https://api.themoviedb.org/3/find/${imdb_id}?external_source=imdb_id&api_key=${process.env.TMDB_API_KEY}`,
      );
      res = await res.json();
      if (imdb_id.startsWith("tt")) {
        return res["movie_results"][0]["poster_path"]
          ? "https://image.tmdb.org/t/p/w185" +
              // @ts-ignore
              res["movie_results"][0]["poster_path"]
          : null;
      } else {
        return res["person_results"][0]["profile_path"]
          ? "https://image.tmdb.org/t/p/w185" +
              // @ts-ignore
              res["person_results"][0]["profile_path"]
          : null;
      }
    }),
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
