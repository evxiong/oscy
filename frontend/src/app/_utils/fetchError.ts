interface Version {
  award: string;
  iteration: number;
  update_stage: string;
  updated_at: string;
  tag: string;
}

export default async function fetchError(url: string) {
  try {
    // const localProductionBuild =
    //   process.env.VERCEL_ENV !== "production" &&
    //   !process.env.VERCEL_URL &&
    //   process.env.NODE_ENV === "production";
    // const base =
    //   process.env.VERCEL_ENV === "production"
    //     ? "https://oscy.vercel.app"
    //     : process.env.VERCEL_URL
    //       ? `https://${process.env.VERCEL_URL}`
    //       : localProductionBuild
    //         ? `http://${process.env.API_HOST}:8000`
    //         : "http://localhost:3000";
    // const finalUrl = localProductionBuild ? url.slice(4) : url;

    const base = process.env.VERCEL_URL
      ? `https://${process.env.VERCEL_URL}`
      : "http://localhost:3000";

    // fetch current version tag, cache for 60s const res = await fetch(base +
    // "/api/version", { next: { revalidate: 60 },
    // });
    // fetch current version tag, cache indefinitely until revalidateTag() is
    // called
    const res = await fetch(base + "/api/version", {
      cache: "force-cache",
      next: {
        revalidate: false,
        tags: ["version"],
      },
    });
    const version: Version = await res.json();

    const fullUrl = new URL(base + url);
    fullUrl.searchParams.set("v", version.tag);
    const data = await fetch(fullUrl);
    if (data.status === 422) {
      return null;
    }
    // console.log(fullUrl.href);
    // console.log(data.headers.get("Cache-Control"));
    // console.log();
    return data.json();
  } catch (error: unknown) {
    if (error instanceof Error) {
      console.error(error.message);
    } else {
      console.error(error);
    }
    throw error;
  }
}
