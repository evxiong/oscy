export default async function fetchError(url: string) {
  try {
    const base =
      process.env.NODE_ENV === "development"
        ? `http://localhost:${process.env.PORT}`
        : process.env.NEXT_PUBLIC_URL;
    const data = await fetch(base + url);
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
