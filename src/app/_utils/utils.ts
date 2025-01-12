import { NominationsType } from "../ceremony/[iteration]/types";

interface TopFive {
  indices: number[];
  imdb_ids: string[];
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
