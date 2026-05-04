const BASE_URL = process.env.VERCEL
  ? `https://${process.env.PROD_API_HOST}`
  : `http://${process.env.LOCAL_API_HOST}:8000`;

/**
 * Fetches data from oscy API.
 *
 * @param relativeUrl API endpoint path + params, ex. `/categories/1`.
 * @returns Promise to JSON response body.
 */
export async function fetchApi(relativeUrl: string) {
  try {
    const currentVersion = await fetchVersion();

    const fullUrl = new URL(BASE_URL + relativeUrl);
    fullUrl.searchParams.set("v", currentVersion.tag);

    const res = await fetch(fullUrl);
    if (!res.ok) {
      console.error(`fetchApi("${relativeUrl}"): HTTP ${res.status} error`);
      return null;
    }

    return res.json();
  } catch (error: unknown) {
    if (error instanceof Error) {
      console.error(error.message);
    } else {
      console.error(error);
    }
    throw error;
  }
}

interface Version {
  award: string;
  iteration: number;
  update_stage: string;
  updated_at: string;
  tag: string;
}

/**
 * Fetches current version, cached indefinitely until `revalidateTag("version")`
 * called.
 *
 * @returns Promise to current Version.
 */
export async function fetchVersion() {
  const res = await fetch(BASE_URL + "/version", {
    cache: "force-cache",
    next: {
      revalidate: false,
      tags: ["version"],
    },
  });
  const version: Version = await res.json();
  return version;
}

interface TMDBResults {
  movie_results: {
    poster_path: string;
  }[];
  person_results: {
    profile_path: string;
  }[];
}

/**
 * Fetches TMDB poster/photo URL using IMDb id.
 *
 * @param imdbId IMDb id of poster/photo to fetch.
 * @param requireResults If true, throw Error if TMDB API returns no results for
 *   the IMDb id; otherwise, returns null. Defaults to false.
 * @returns Promise to full image URL of TMDB poster/photo, or null if no image
 *   found and `requireResults` is false.
 */
export async function fetchImageUrl(
  imdbId: string,
  requireResults: boolean = false,
) {
  const baseImageUrl = "https://image.tmdb.org/t/p/w185";

  const r = await fetch(
    `https://api.themoviedb.org/3/find/${imdbId}?external_source=imdb_id&api_key=${process.env.TMDB_API_KEY}`,
  );
  if (!r.ok) {
    throw new Error(
      `Failed to connect to TMDB API: check validity of TMDB_API_KEY in .env`,
    );
  }

  const results: TMDBResults = await r.json();
  if (imdbId.startsWith("tt")) {
    if (
      results.movie_results.length > 0 &&
      results.movie_results[0].poster_path
    ) {
      return baseImageUrl + results.movie_results[0].poster_path;
    }

    if (requireResults) {
      throw new Error(`No movie results in TMDB for IMDb id: ${imdbId}`);
    } else {
      return null;
    }
  } else {
    if (
      results.person_results.length > 0 &&
      results.person_results[0].profile_path
    ) {
      return baseImageUrl + results.person_results[0].profile_path;
    }

    if (requireResults) {
      throw new Error(`No person results in TMDB for IMDb id: ${imdbId}`);
    } else {
      return null;
    }
  }
}
