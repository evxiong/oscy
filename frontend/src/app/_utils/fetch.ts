interface Version {
  award: string;
  iteration: number;
  update_stage: string;
  updated_at: string;
  tag: string;
}

const BASE_URL = process.env.VERCEL
  ? `https://${process.env.PROD_API_HOST}`
  : `http://${process.env.LOCAL_API_HOST}:8000`;

export async function fetchApi(relativeUrl: string) {
  try {
    const currentVersion = await fetchVersion();

    const fullUrl = new URL(BASE_URL + relativeUrl);
    fullUrl.searchParams.set("v", currentVersion.tag);

    const res = await fetch(fullUrl);
    if (!res.ok) {
      throw new Error(`HTTP error: ${res.status}`);
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

export async function fetchVersion() {
  // fetch current version tag, cache indefinitely until revalidateTag() is
  // called
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
