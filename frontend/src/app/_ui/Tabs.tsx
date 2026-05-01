"use client";

import {
  Tab as AriaTab,
  TabList as AriaTabList,
  TabListProps as AriaTabListProps,
  TabPanel as AriaTabPanel,
  TabPanelProps as AriaTabPanelProps,
  TabPanels as AriaTabPanels,
  TabProps as AriaTabProps,
  Tabs as AriaTabs,
  TabsProps as AriaTabsProps,
  composeRenderProps,
} from "react-aria-components";
import merge from "../_utils/merge";

export function Tabs({ className, ...props }: AriaTabsProps) {
  return (
    <AriaTabs className={merge("group flex flex-col", className)} {...props} />
  );
}

export function TabList<T extends object>({
  className,
  ...props
}: AriaTabListProps<T>) {
  return (
    <AriaTabList
      className={merge(
        "hide-scrollbar -mx-1 inline-flex w-full items-center gap-6 overflow-x-auto border-border px-1 text-secondary",
        className,
      )}
      {...props}
    />
  );
}

export function Tab({ className, children, ...props }: AriaTabProps) {
  return (
    <AriaTab
      className={merge(
        "group relative my-1 inline-flex cursor-pointer justify-center whitespace-nowrap text-base font-medium",
        "outline-offset-2 data-[focus-visible]:outline data-[focus-visible]:outline-2 data-[focus-visible]:outline-ring",
        "data-[hovered]:text-primary data-[hovered]:transition-none",
        "transition-colors duration-200 data-[selected]:text-primary",
        className,
      )}
      {...props}
    >
      {composeRenderProps(children, (children) => (
        <>
          {children}
          <div className="invisible absolute -bottom-1 left-1/2 right-1/2 h-0.5 rounded-b-full bg-gold transition-all duration-200 ease-in-out group-data-[selected]:visible group-data-[selected]:left-0 group-data-[selected]:right-0"></div>
        </>
      ))}
    </AriaTab>
  );
}

export const TabPanels = AriaTabPanels;

export function TabPanel({ className, ...props }: AriaTabPanelProps) {
  return (
    <AriaTabPanel
      className={merge(
        "data-[inert]:hidden",
        "data-[focus-visible]:outline-none data-[focus-visible]:ring-2 data-[focus-visible]:ring-ring data-[focus-visible]:ring-offset-2",
        className,
      )}
      {...props}
    />
  );
}
