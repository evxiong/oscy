import { CeremonyType } from "@/app/ceremony/[iteration]/types";

export interface Entity {
  id: number;
  imdb_id: string;
  type: string;
  name: string;
  aliases: string[];
  total_noms: number;
  total_wins: number;
  nominations: CeremonyType[];
  rankings: EntityRankings;
}

export interface EntityRankings {
  category_rankings: CategoryRankings[];
  category_group_rankings: CategoryGroupRankings[];
  overall_rankings: OverallRankings;
}

export interface CategoryRankings {
  category_id: number;
  category: string;
  category_noms: number;
  category_wins: number;
  category_noms_rank: number;
  category_wins_rank: number;
}

export interface CategoryGroupRankings {
  category_group_id: number;
  category_group: string;
  category_group_noms: number;
  category_group_wins: number;
  category_group_noms_rank: number;
  category_group_wins_rank: number;
}

export interface OverallRankings {
  overall_noms: number;
  overall_wins: number;
  overall_noms_rank: number;
  overall_wins_rank: number;
}
