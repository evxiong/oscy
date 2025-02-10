import Link from "next/link";

interface Breadcrumb {
  name: string;
  link: string;
}

export default function Breadcrumbs({ crumbs }: { crumbs: Breadcrumb[] }) {
  return (
    <div className="flex flex-row gap-1 text-xs font-medium leading-5">
      {crumbs.map((c, i) => {
        const isFinal = c.link === "" || i === crumbs.length - 1;
        return (
          <div key={i} className="flex flex-row gap-1">
            <Link
              prefetch={false}
              href={c.link}
              aria-disabled={isFinal}
              tabIndex={isFinal ? -1 : undefined}
              className={`${isFinal ? "pointer-events-none text-zinc-500" : "text-zinc-400 hover:text-gold focus:text-gold"}`}
            >
              {c.name}
            </Link>
            {i !== crumbs.length - 1 && (
              <div className="select-none text-zinc-300">/</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
