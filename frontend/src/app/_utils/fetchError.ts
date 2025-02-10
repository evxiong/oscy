export default async function fetchError(url: string) {
  try {
    const data = await fetch(url);
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
