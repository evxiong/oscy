import { NominationsType } from "@/app/ceremony/[iteration]/types";

export interface CategoryGroupInfo {
  category_group_id: number;
  category_group: string;
  categories: CategoryInfo[];
}

export interface CategoryInfo {
  category_id: number;
  category: string;
  category_names: CategoryNameInfo[];
}

export interface CategoryNameInfo {
  category_name_id: number;
  official_name: string;
  common_name: string;
}

export interface Category {
  category_id: number;
  category: string;
  category_group_id: number;
  category_group: string;
  category_names: CategoryName[];
  nominations: NominationsType;
}

export interface CategoryName {
  category_name_id: number;
  official_name: string;
  common_name: string;
  ranges: [number, number][];
}
