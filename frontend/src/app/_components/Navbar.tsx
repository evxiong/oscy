import { IconApi, IconBrandGithub } from "@tabler/icons-react";
import Link from "next/link";
import { fetchVersion } from "../_utils/fetch";
import ExternalLink from "./ExternalLink";
import SearchBar from "./SearchBar";

export default async function Navbar() {
  const currentEdition = (await fetchVersion()).iteration;
  return (
    <header className="flex h-20 w-full select-none flex-row justify-center">
      <div className="flex w-full flex-row items-center gap-6">
        <div className="flex-1 select-none pb-1 pl-6 text-2xl">
          <Link
            href="/"
            className="w-fit cursor-pointer tracking-tight text-primary transition-colors hover:text-gold focus-visible:text-gold"
          >
            oscy
          </Link>
        </div>
        <SearchBar currentEdition={currentEdition} />
        <div className="flex flex-1 flex-row justify-end gap-2 pr-6">
          <ExternalLink
            aria-label="API docs"
            href="/api/docs"
            className="group flex size-8 cursor-pointer items-center justify-center"
          >
            <IconApi
              aria-hidden
              className="size-5 stroke-secondary transition-colors group-hover:stroke-gold group-focus-visible:stroke-gold"
            />
          </ExternalLink>
          <ExternalLink
            aria-label="GitHub repo"
            href="https://github.com/evxiong/oscy"
            className="group flex size-8 cursor-pointer items-center justify-center"
          >
            <IconBrandGithub
              aria-hidden
              className="size-5 stroke-secondary transition-colors group-hover:stroke-gold group-focus-visible:stroke-gold"
            />
          </ExternalLink>
        </div>
      </div>
    </header>
  );
}
