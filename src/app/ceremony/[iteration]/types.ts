export enum AwardType {
  oscar = 0,
  emmy = 1,
}

export interface EditionType {
  id: number;
  iteration: number;
  official_year: string;
  ceremony_date: string;
}

export interface NominationsType {
  editions: CeremonyType[];
  stats: AllStatsType;
}

export interface AllStatsType {
  title_stats: TitleStatsType[];
  entity_stats: EntityStatsType[];
}

export interface StatsType {
  id: number;
  imdb_id: string;
}

export interface TitleStatsType extends StatsType {
  title: string;
  noms: number;
  wins: number;
}

export interface EntityStatsType extends StatsType {
  name: string;
  category_id: number;
  category_noms: number;
  category_wins: number;
  total_noms: number;
  total_wins: number;
  career_category_noms: number;
  career_category_wins: number;
  career_total_noms: number;
  career_total_wins: number;
}

export interface CeremonyType {
  id: number;
  iteration: number;
  official_year: string;
  ceremony_date: string;
  edition_noms: number;
  edition_wins: number;
  categories: CategoryType[];
}

export interface CategoryType {
  category_id: number;
  category_group: string;
  official_name: string;
  common_name: string;
  short_name: string;
  category_noms: number;
  category_wins: number;
  nominees: NomineeType[];
}

export interface NomineeType {
  winner: boolean;
  titles: TitleType[];
  people: PersonType[];
  statement: string;
  is_person: boolean;
  note: string;
  official: boolean;
  stat: boolean;
}

export interface TitleType {
  id: number;
  title: string;
  imdb_id: string;
  detail: string[];
  title_winner: boolean;
}

export interface PersonType {
  id: number;
  name: string;
  imdb_id: string;
  statement_ind: number;
}
