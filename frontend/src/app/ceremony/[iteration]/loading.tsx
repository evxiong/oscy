import Skeleton from "@/app/_ui/Skeleton";
import { Fragment } from "react";

export default function CeremonyLoading() {
  return (
    <div className="flex flex-col gap-5">
      <div className="flex w-full flex-col overflow-x-auto bg-gradient-to-r from-background to-overlay py-5 md:items-center">
        <div className="w-fit px-6 md:w-[768px]">
          <div className="flex flex-row gap-[11.25px]">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="flex w-[135px] flex-shrink-0 flex-col gap-2"
              >
                <Skeleton className="h-3 w-20" />
                <Skeleton className="relative h-[200px] overflow-hidden rounded-[0.25rem]" />
                <div className="flex flex-col gap-1">
                  <div>
                    <div className="flex h-4 items-center">
                      <Skeleton className="h-3 w-28" />
                    </div>
                    <div className="flex h-4 items-center">
                      <Skeleton className="h-3 w-14" />
                    </div>
                  </div>
                  <div>
                    <div className="flex h-3.5 items-center">
                      <Skeleton className="h-2.5 w-24" />
                    </div>
                    <div className="flex h-3.5 items-center">
                      <Skeleton className="h-2.5 w-14" />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="mb-20 flex w-full flex-col items-center">
        <div className="w-full px-6 md:w-[768px]">
          <Skeleton className="-mb-2 h-4 w-60" />
          <div className="hide-scrollbar sticky top-0 z-30 flex h-[--nominations-header-height-mobile] flex-col justify-center gap-3 overflow-x-auto sm:h-[--nominations-header-height] sm:flex-row sm:items-center sm:gap-6">
            <div className="sm:flex-1">
              <Skeleton className="h-6 w-full" />
            </div>
            <div className="flex sm:flex-1 sm:justify-end">
              <Skeleton className="h-4 w-32" />
            </div>
          </div>
          <hr />
          {[...Array(4)].map((_, i) => (
            <Fragment key={i}>
              <div className="flex flex-col gap-1 py-6 sm:flex-row sm:gap-6">
                <div className="sticky top-[--nominations-header-height-mobile] z-10 w-full flex-1 bg-white pb-4 sm:top-[--nominations-header-height] sm:pb-0">
                  <div className="sticky top-[--nominations-header-height-mobile] z-10 sm:top-[--nominations-header-height]">
                    <Skeleton className="h-6 w-60" />
                  </div>
                </div>
                <div className="flex flex-1 flex-col gap-[0.875rem]">
                  {[...Array(5)].map((_, j) => (
                    <div key={j} className="flex flex-row gap-2.5">
                      <div className="size-4 shrink-0" />
                      <div className="flex flex-col gap-1">
                        <div className="flex h-5 items-center">
                          <Skeleton className="h-4 w-24" />
                        </div>
                        <div className="flex h-4 items-center">
                          <Skeleton className="h-3.5 w-64" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <hr />
            </Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}
