export default async function fetchError(url: string) {
  try {
    const localProductionBuild =
      process.env.VERCEL_ENV !== "production" &&
      !process.env.VERCEL_URL &&
      process.env.NODE_ENV === "production";
    const base =
      process.env.VERCEL_ENV === "production"
        ? "https://oscy.vercel.app"
        : process.env.VERCEL_URL
          ? `https://${process.env.VERCEL_URL}`
          : localProductionBuild
            ? `http://${process.env.API_HOST}:8000`
            : "http://localhost:3000";

    const finalUrl = localProductionBuild ? url.slice(4) : url;
    const data = await fetch(base + finalUrl);
    if (data.status === 422) {
      return null;
    }
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
