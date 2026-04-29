import type {
  CategoryType,
  NominationsType,
} from "../ceremony/[iteration]/types";
import { fetchImageUrl } from "./fetch";

interface TopFiveCard {
  category_ind: number;
  nominee_ind: number;
  imdb_id: string;
}

export function ceremonyToTopFive(
  nominations: NominationsType,
): TopFiveCard[] | null {
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

  const topFive: TopFiveCard[] = indices.map((categoryInd, i) => ({
    category_ind: categoryInd,
    nominee_ind: 0,
    imdb_id: imdb_ids[i],
  }));

  return topFive;
}

export function categoriesToTopFive(categories: CategoryType[]): TopFiveCard[] {
  // categories should already be reversed
  const topFiveCards: TopFiveCard[] = [];

  for (let categoryInd = 0; categoryInd < categories.length; categoryInd++) {
    const category = categories[categoryInd];

    if (category.nominees[0].pending) {
      categoryInd += 1;
      continue;
    }

    for (
      let nomineeInd = 0;
      nomineeInd < category.nominees.length;
      nomineeInd++
    ) {
      const nominee = category.nominees[nomineeInd];

      if (!nominee.winner) {
        break;
      }
      if (nominee.is_person || category.short_name === "Director") {
        topFiveCards.push({
          category_ind: categoryInd,
          nominee_ind: nomineeInd,
          imdb_id: nominee.people[0]?.imdb_id ?? nominee.titles[0].imdb_id,
        });
      } else {
        topFiveCards.push({
          category_ind: categoryInd,
          nominee_ind: nomineeInd,
          imdb_id: nominee.titles[0]?.imdb_id ?? nominee.people[0].imdb_id,
        });
      }
      if (topFiveCards.length === 5) {
        break;
      }
    }

    if (topFiveCards.length === 5) {
      break;
    }
  }

  return topFiveCards;
}

export async function topFiveToImageUrls(
  topFive: TopFiveCard[],
): Promise<(string | null)[]> {
  try {
    if (!process.env.TMDB_API_KEY) {
      return topFive.map((_) => null);
    }

    return Promise.all(
      topFive.map((topFiveCard) => fetchImageUrl(topFiveCard.imdb_id)),
    );
  } catch (error: unknown) {
    if (error instanceof Error) {
      console.error(error.message);
    } else {
      console.error(error);
    }
    return topFive.map((_) => null);
  }
}
