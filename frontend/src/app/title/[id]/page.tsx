import EntityTitle from "@/app/_components/entityTitle";
import fetchError from "@/app/_utils/fetchError";
import { EntityOrTitle } from "@/app/entity/[id]/types";
import { Metadata } from "next";
import { notFound } from "next/navigation";

export async function generateStaticParams() {
  return [];
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const titleId = (await params).id;
  const title: EntityOrTitle = await fetchError(`/api/titles/${titleId}`);
  if (title === null) {
    notFound();
  }

  const t = `${title.name} - Nominations & Statistics`;
  const description = `Browse nominations and stats received by ${title.name}.`;

  return {
    title: t,
    description: description,
    openGraph: {
      siteName: "oscy",
      title: t,
      description: description,
      type: "article",
      url: `/title/${title.id}`,
    },
    twitter: {
      card: "summary",
      title: t,
      description: description,
    },
  };
}

export default async function Title({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const titleId = (await params).id;
  const title: EntityOrTitle = await fetchError(`/api/titles/${titleId}`);
  if (title === null) {
    notFound();
  }
  return <EntityTitle isTitle={true} entityOrTitle={title} />;
}
