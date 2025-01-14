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
}
