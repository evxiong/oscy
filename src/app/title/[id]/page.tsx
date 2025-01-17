import EntityTitle from "@/app/_components/entityTitle";
import fetchError from "@/app/_utils/fetchError";
import { EntityOrTitle } from "@/app/entity/[id]/types";
import { notFound } from "next/navigation";

export default async function Title({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const titleId = (await params).id;
  const title: EntityOrTitle = await fetchError(
    `http://localhost:8000/title/${titleId}`,
  );
  if (title === null) {
    notFound();
  }
  return <EntityTitle isTitle={true} entityOrTitle={title} />;
}
