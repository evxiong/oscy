export interface SearchResults {
  titles: SearchGroup;
  entities: SearchGroup;
  categories: SearchGroup;
  ceremonies: SearchGroup;
}

export interface Result {
  id: number;
  name: string;
  subdir: string;
  type: string;
  word_dist: number;
  dist: number;
}

export interface SearchGroup {
  page: number;
  next_page: number | null;
  page_size: number;
  length: number;
  results: EntityResult[] | TitleResult[] | CategoryResult[] | CeremonyResult[];
}

export interface EntityResult {
  id: number;
  imdb_id: string;
  type: string;
  name: string;
  aliases: string[];
  occurrences: number;
  iterations: number[];
  noms: number;
  wins: number;
  word_dist: number;
  dist: number;
}

export interface TitleResult {
  id: number;
  imdb_id: string;
  type: string;
  title: string;
  iterations: number[];
  noms: number;
  wins: number;
  word_dist: number;
  dist: number;
}

export interface CategoryResult {
  id: number;
  category: string;
  category_group_id: number;
  category_group: string;
  word_dist: number;
  dist: number;
}

export interface CeremonyResult {
  id: number;
  iteration: number;
  official_year: string;
  ceremony_date: string;
  word_dist: number;
  dist: number;
}
