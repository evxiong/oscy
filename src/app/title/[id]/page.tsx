import EntityTitle from "@/app/_components/entityTitle";
import { EntityOrTitle } from "@/app/entity/[id]/types";

export default async function Title({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const titleId = (await params).id;
  const titleData = await fetch(`http://localhost:8000/title/${titleId}`);
  const title: EntityOrTitle = await titleData.json();
  return <EntityTitle isTitle={true} entityOrTitle={title} />;
}
