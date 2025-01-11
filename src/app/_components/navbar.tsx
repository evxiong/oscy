import { Input } from "@headlessui/react";
import { IconBrandGithub, IconSearch, IconApi } from "@tabler/icons-react";

export default function Navbar() {
  return (
    <header className="flex h-20 w-full select-none flex-row justify-center">
      <div className="flex w-full flex-row items-center">
        {/*md:max-w-3xl*/}
        <div className="flex-1 select-none pb-1 pl-6 text-2xl">
          <a
            href="/"
            className="w-fit cursor-pointer tracking-tight text-zinc-800 hover:text-gold"
          >
            oscy
          </a>
        </div>
        <div className="flex h-9 flex-row items-center rounded-md bg-zinc-100 has-[input:focus-within]:outline has-[input:focus-within]:outline-2 has-[input:focus-within]:-outline-offset-2 has-[input:focus-within]:outline-gold md:w-[720px]">
          <IconSearch className="mx-2 h-4 w-4 stroke-zinc-400" />
          <Input
            name="Search"
            type="text"
            placeholder="Search for titles or people"
            className="h-9 w-full bg-transparent pr-2 text-sm text-zinc-800 outline-none"
          />
          {/* <div className="group flex h-8 w-8 cursor-pointer items-center justify-center rounded-full">
            <IconSearch className="group-hover:stroke-gold h-5 w-5 stroke-zinc-500" />
          </div> */}
        </div>
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
