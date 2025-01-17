import { notFound } from "next/navigation";
import { EntityOrTitle } from "./types";
import EntityTitle from "@/app/_components/entityTitle";
import fetchError from "@/app/_utils/fetchError";

export default async function Entity({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const entityId = (await params).id;
  const entity: EntityOrTitle = await fetchError(
    `http://localhost:8000/entity/${entityId}`,
  );
  if (entity === null) {
    notFound();
  }
  return <EntityTitle isTitle={false} entityOrTitle={entity} />;
}
