"use client";

import Link from "next/link";
import { useState } from "react";

export default function PrefetchLink({
  href,
  children,
  ...props
}: React.ComponentProps<typeof Link>) {
  // prefetch link on hover only
  // see https://nextjs.org/docs/15/app/guides/prefetching#hover-triggered-prefetch
  const [hover, setHover] = useState(false);
  return (
    <Link
      href={href}
      prefetch={hover ? null : false}
      onMouseEnter={() => setHover(true)}
      {...props}
    >
      {children}
    </Link>
  );
}
