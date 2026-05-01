import Link from "next/link";

interface Breadcrumb {
  name: string;
  link: string;
}

export default function Breadcrumbs({ crumbs }: { crumbs: Breadcrumb[] }) {
  return (
    <ol
      aria-label="Breadcrumb"
      className="flex flex-row gap-1 text-xs/5 font-medium"
    >
      {crumbs.map((c, i) => {
        const isFinal = c.link === "" || i === crumbs.length - 1;
        return (
          <li key={i} className="flex flex-row gap-1">
            <Link
              prefetch={false}
              href={c.link}
              aria-disabled={isFinal}
              tabIndex={isFinal ? -1 : undefined}
              className={`${isFinal ? "pointer-events-none text-secondary" : "text-tertiary hover:text-gold focus:text-gold"}`}
              {...(isFinal && { "aria-current": "page" })}
            >
              {c.name}
            </Link>
            {i !== crumbs.length - 1 && (
              <span aria-hidden className="select-none text-underline">
                /
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
