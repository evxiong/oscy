import { IconBrandGithub, IconApi } from "@tabler/icons-react";
import SearchBar from "./searchBar";

export default function Navbar() {
  return (
    <header className="flex h-20 w-full select-none flex-row justify-center">
      <div className="flex w-full flex-row items-center">
        <div className="flex-1 select-none pb-1 pl-6 text-2xl">
          <a
            href="/"
            className="w-fit cursor-pointer tracking-tight text-zinc-800 hover:text-gold"
          >
            oscy
          </a>
        </div>
        <SearchBar />
        <div className="flex flex-1 flex-row justify-end gap-2 pr-6">
          <a className="group flex h-8 w-8 cursor-pointer items-center justify-center rounded-full">
            <IconApi className="h-5 w-5 stroke-zinc-500 group-hover:stroke-gold" />
          </a>
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://github.com/evxiong/oscy"
            className="group flex h-8 w-8 cursor-pointer items-center justify-center rounded-full"
          >
            <IconBrandGithub className="h-5 w-5 stroke-zinc-500 group-hover:stroke-gold" />
          </a>
        </div>
      </div>
    </header>
  );
}
