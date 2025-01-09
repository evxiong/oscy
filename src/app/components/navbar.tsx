import { Input } from "@headlessui/react";
import { IconBrandGithub, IconSearch, IconApi } from "@tabler/icons-react";

export default function Navbar() {
  return (
    <header className="flex h-20 w-full select-none flex-row justify-center">
      <div className="flex w-full flex-row items-center">
        {/*md:max-w-3xl*/}
        <div className="flex-1 pl-6">
          {/* <Input name="Search" type="text" className="border border-zinc-300" /> */}
          <div className="group flex h-8 w-8 cursor-pointer items-center justify-center rounded-full">
            <IconSearch className="group-hover:stroke-gold h-5 w-5 stroke-zinc-500" />
          </div>
        </div>
        <div className="pb-1 text-2xl">oscy</div>
        <div className="flex flex-1 flex-row justify-end gap-2 pr-6">
          <a className="group flex h-8 w-8 cursor-pointer items-center justify-center rounded-full">
            <IconApi className="group-hover:stroke-gold h-5 w-5 stroke-zinc-500" />
          </a>
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://github.com/evxiong/oscy"
            className="group flex h-8 w-8 cursor-pointer items-center justify-center rounded-full"
          >
            <IconBrandGithub className="group-hover:stroke-gold h-5 w-5 stroke-zinc-500" />
          </a>
        </div>
      </div>
    </header>
  );
}
