import { IconArrowBackUp } from "@tabler/icons-react";
import { Metadata } from "next";
import Link from "next/link";
import ExploreButton from "./_components/ExploreButton";
import { buttonVariants } from "./_ui/variants";

export const metadata: Metadata = {
  title: "Page not found",
};

export default function NotFound() {
  return (
    <div className="flex flex-col">
      <section className="mb-10 flex w-full flex-col items-center gap-8 py-16">
        <div className="flex w-full flex-col items-center gap-8 px-6 md:w-[768px]">
          <div>
            <h1 className="text-center text-4xl font-medium tracking-tight text-title">
              We couldn&rsquo;t find that page&hellip;
            </h1>
            <h3 className="mt-3 text-center text-xl/6 font-normal tracking-tight text-secondary">
              Double-check the URL.
            </h3>
          </div>
          <div className="flex flex-row gap-4">
            <Link href="/" className={buttonVariants({ variant: "primary" })}>
              <IconArrowBackUp />
              <span className="hidden xxs:block">Back to home</span>
              <span className="xxs:hidden">Home</span>
            </Link>
            <ExploreButton id="explore-not-found">
              <span>New search</span>
            </ExploreButton>
          </div>
        </div>
      </section>
    </div>
  );
}
