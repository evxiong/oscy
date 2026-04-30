"use client";

import { IconReload } from "@tabler/icons-react";
import { useRouter } from "next/navigation";
import { startTransition, useEffect } from "react";
import ExploreButton from "./_components/ExploreButton";
import Button from "./_ui/Button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    console.error(error);
  }, [error]);

  function refresh() {
    startTransition(() => {
      router.refresh();
      reset();
    });
  }

  return (
    <div className="flex flex-col">
      <section className="mb-10 flex w-full flex-col items-center gap-8 py-16">
        <div className="flex w-full flex-col items-center gap-8 px-6 md:w-[768px]">
          <div>
            <h1 className="text-center text-4xl font-medium tracking-tight text-title">
              Something went wrong&hellip;
            </h1>
            <h3 className="mt-3 text-center text-xl/6 font-normal tracking-tight text-secondary">
              We encountered an error while trying to retrieve that page.
            </h3>
          </div>
          <div className="flex flex-row gap-4">
            <Button onClick={refresh} variant="primary">
              <IconReload />
              <span>Try again</span>
            </Button>
            <ExploreButton id="explore-error">
              <span>New search</span>
            </ExploreButton>
          </div>
        </div>
      </section>
    </div>
  );
}
