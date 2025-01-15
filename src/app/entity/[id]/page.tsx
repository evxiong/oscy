import { EntityOrTitle } from "./types";
import EntityTitle from "@/app/_components/entityTitle";

export default async function Entity({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const entityId = (await params).id;
  const entityData = await fetch(`http://localhost:8000/entity/${entityId}`);
  const entity: EntityOrTitle = await entityData.json();
  return <EntityTitle isTitle={false} entityOrTitle={entity} />;
}
