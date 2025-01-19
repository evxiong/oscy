import Link from "next/link";
import ExploreButton from "./_components/exploreButton";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Page not found | oscy",
};

export default function NotFound() {
  return (
    <div className="flex flex-col">
      <section className="mb-10 flex w-full flex-col items-center gap-8 py-16">
        <div className="flex w-full flex-col items-center gap-8 px-6 md:w-[768px]">
          <div>
            <h1 className="text-center text-4xl font-medium tracking-tight text-zinc-600">
              We couldn&rsquo;t find that page&hellip;
            </h1>
            <h3 className="mt-3 text-center text-xl font-normal leading-6 tracking-tight text-zinc-500">
              Double-check the URL.
            </h3>
          </div>
          <div className="flex flex-row gap-4">
            <Link
              href="/"
              className="flex cursor-pointer flex-row items-center gap-2 rounded-md border border-zinc-400 px-4 py-2 text-sm font-medium text-zinc-500 hover:border-zinc-800 hover:text-zinc-800 focus:border-zinc-800 focus:text-zinc-800 focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
            >
              <span>Back to home</span>
            </Link>
            <ExploreButton id="explore-3" text="New search" />
          </div>
        </div>
      </section>
    </div>
  );
}
