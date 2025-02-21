import { notFound } from "next/navigation";
import { EntityOrTitle } from "./types";
import EntityTitle from "@/app/_components/entityTitle";
import fetchError from "@/app/_utils/fetchError";
import { Metadata } from "next";

export async function generateStaticParams() {
  return [];
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const entityId = (await params).id;
  const entity: EntityOrTitle = await fetchError(
    `http://localhost:8000/entities/${entityId}`,
  );
  if (entity === null) {
    notFound();
  }

  const title = `${entity.name} - Nominations & Statistics`;
  const description = `Browse nominations and stats received by ${entity.name}.`;

  return {
    title: title,
    description: description,
    openGraph: {
      siteName: "oscy",
      title: title,
      description: description,
      type: "article",
      url: `/entity/${entity.id}`,
    },
    twitter: {
      card: "summary",
      title: title,
      description: description,
    },
  };
}

export default async function Entity({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const entityId = (await params).id;
  const entity: EntityOrTitle = await fetchError(
    `http://localhost:8000/entities/${entityId}`,
  );
  if (entity === null) {
    notFound();
  }
  return <EntityTitle isTitle={false} entityOrTitle={entity} />;
}
