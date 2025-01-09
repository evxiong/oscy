import { TabGroup, TabList, Tab, TabPanels, TabPanel } from "@headlessui/react";
import {
  IconStarFilled,
  IconArrowLeft,
  IconArrowRight,
} from "@tabler/icons-react";

export default function Home() {
  return (
    <div className="flex flex-col gap-5">
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full flex-col gap-4 px-6 pt-5 md:w-[768px]">
          <nav className="flex flex-row justify-between text-xs font-medium text-zinc-500 underline decoration-zinc-300 underline-offset-4">
            <div>Ceremonies</div>
            <div className="flex flex-row gap-4">
              <div>Academy Awards</div>
              <div>2023 (96th)</div>
            </div>
          </nav>
          <div className="flex w-full flex-row items-center justify-between">
            <div className="flex flex-col">
              <h1 className="text-2xl font-medium text-zinc-800">
                96th Academy Awards
              </h1>
              <h2 className="text-sm font-medium text-zinc-500">
                March 10, 2024 · Honoring films from 2023
              </h2>
            </div>
            <div className="hidden flex-row gap-2 sm:flex">
              <div className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-zinc-100 hover:bg-zinc-200">
                <IconArrowLeft className="h-5 w-5 stroke-zinc-500" />
              </div>
              <div className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-zinc-100 hover:bg-zinc-200">
                <IconArrowRight className="h-5 w-5 stroke-zinc-500" />
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="flex w-full flex-col overflow-x-auto bg-gradient-to-r from-white to-zinc-100 px-6 py-5 md:items-center">
        <div className="grid w-[720px] grid-cols-5 gap-3">
          <Card
            category="Best Picture"
            title="Oppenheimer"
            names={["Emma Thomas", "Charles Roven", "Christopher Nolan"]}
            title_first={true}
          />
          <Card
            category="Best Director"
            title="Oppenheimer"
            names={["Christopher Nolan"]}
            title_first={false}
          />
          <Card
            category="Best Actor"
            title="Oppenheimer"
            names={["Cillian Murphy"]}
            title_first={false}
          />
          <Card
            category="Best Actress"
            title="Poor Things"
            names={["Emma Stone"]}
            title_first={false}
          />
          <Card
            category="Best Original Screenplay"
            title="Anatomy of a Fall"
            names={["Justine Triet", "Arthur Harari"]}
            title_first={true}
          />
        </div>
      </section>
      <section className="flex w-full flex-col items-center">
        <div className="flex w-full px-6 md:w-[768px]">
          <TabGroup className="w-full">
            <TabList className="mb-0.5 flex flex-row gap-7 text-base font-medium text-zinc-500">
              <Tab className="decoration-zinc-500 underline-offset-[6px] data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                Nominations
              </Tab>
              <Tab className="decoration-zinc-500 underline-offset-[6px] data-[selected]:font-semibold data-[hover]:text-zinc-800 data-[selected]:text-zinc-800 data-[selected]:underline">
                Statistics
              </Tab>
            </TabList>
            <div className="sticky top-0 z-20 flex h-14 flex-row items-center justify-between bg-white text-sm font-medium text-zinc-500">
              <div className="flex flex-row gap-4">
                <div>All</div>
                <div>Category: All</div>
              </div>
              <div className="font-semibold">2023 (96th)</div>
            </div>
            <TabPanels>
              <TabPanel>
                <hr />
                <div className="flex flex-col gap-1 py-6 text-zinc-800 sm:flex-row sm:gap-5">
                  <div className="sticky top-14 flex-1 bg-white pb-4">
                    <h1 className="hover:text-gold sticky top-14 flex w-fit cursor-pointer text-xl font-medium leading-6 sm:text-lg sm:leading-6">
                      Best Actor in a Leading Role
                    </h1>
                  </div>
                  <div className="flex flex-1 flex-col gap-3">
                    <Nominee
                      winner={false}
                      titles={["Maestro"]}
                      names={["Bradley Cooper"]}
                      roles={["Leonard Bernstein"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["Rustin"]}
                      names={["Colman Domingo"]}
                      roles={["Bayard Rustin"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["The Holdovers"]}
                      names={["Paul Giamatti"]}
                      roles={["Paul Hunham"]}
                    />
                    <Nominee
                      winner={true}
                      titles={["Oppenheimer"]}
                      names={["Cillian Murphy"]}
                      roles={["J. Robert Oppenheimer"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["American Fiction"]}
                      names={["Jeffrey Wright"]}
                      roles={['Thelonius "Monk" Ellison']}
                    />
                  </div>
                </div>
                <hr />
                <div className="flex flex-col gap-1 py-6 text-zinc-800 sm:flex-row sm:gap-5">
                  <div className="sticky top-14 flex-1 bg-white pb-4">
                    <h1 className="hover:text-gold sticky top-14 flex w-fit cursor-pointer text-xl font-medium leading-6 sm:text-lg sm:leading-6">
                      Best Actor in a Supporting Role
                    </h1>
                  </div>
                  <div className="flex flex-1 flex-col gap-3">
                    <Nominee
                      winner={false}
                      titles={["Maestro"]}
                      names={["Bradley Cooper"]}
                      roles={["Leonard Bernstein"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["Rustin"]}
                      names={["Colman Domingo"]}
                      roles={["Bayard Rustin"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["The Holdovers"]}
                      names={["Paul Giamatti"]}
                      roles={["Paul Hunham"]}
                    />
                    <Nominee
                      winner={true}
                      titles={["Oppenheimer"]}
                      names={["Cillian Murphy"]}
                      roles={["J. Robert Oppenheimer"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["American Fiction"]}
                      names={["Jeffrey Wright"]}
                      roles={['Thelonius "Monk" Ellison']}
                    />
                  </div>
                </div>
                <hr />
                <div className="flex flex-col gap-1 py-6 text-zinc-800 sm:flex-row sm:gap-5">
                  <div className="sticky top-14 flex-1 bg-white pb-4">
                    <h1 className="hover:text-gold sticky top-14 flex w-fit cursor-pointer text-xl font-medium leading-6 sm:text-lg sm:leading-6">
                      Best Screenplay Written Directly for the Screen—based on
                      factual material or on story material not previously
                      published or produced
                    </h1>
                  </div>
                  <div className="flex flex-1 flex-col gap-3">
                    <Nominee
                      winner={false}
                      titles={["Maestro"]}
                      names={["Bradley Cooper"]}
                      roles={["Leonard Bernstein"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["Rustin"]}
                      names={["Colman Domingo"]}
                      roles={["Bayard Rustin"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["The Holdovers"]}
                      names={["Paul Giamatti"]}
                      roles={["Paul Hunham"]}
                    />
                    <Nominee
                      winner={true}
                      titles={["Oppenheimer"]}
                      names={["Cillian Murphy"]}
                      roles={["J. Robert Oppenheimer"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["American Fiction"]}
                      names={["Jeffrey Wright"]}
                      roles={['Thelonius "Monk" Ellison']}
                    />
                  </div>
                </div>
                <hr />
                <div className="flex flex-col gap-1 py-6 text-zinc-800 sm:flex-row sm:gap-5">
                  <div className="sticky top-14 flex-1 bg-white pb-4">
                    <h1 className="hover:text-gold sticky top-14 flex w-fit cursor-pointer text-xl font-medium leading-6 sm:text-lg sm:leading-6">
                      Best Screenplay Written Directly for the Screen—based on
                      factual material or on story material not previously
                      published or produced
                    </h1>
                  </div>
                  <div className="flex flex-1 flex-col gap-3">
                    <Nominee
                      winner={false}
                      titles={["Maestro"]}
                      names={["Bradley Cooper"]}
                      roles={["Leonard Bernstein"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["Rustin"]}
                      names={["Colman Domingo"]}
                      roles={["Bayard Rustin"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["The Holdovers"]}
                      names={["Paul Giamatti"]}
                      roles={["Paul Hunham"]}
                    />
                    <Nominee
                      winner={true}
                      titles={["Oppenheimer"]}
                      names={["Cillian Murphy"]}
                      roles={["J. Robert Oppenheimer"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["American Fiction"]}
                      names={["Jeffrey Wright"]}
                      roles={['Thelonius "Monk" Ellison']}
                    />
                  </div>
                </div>
                <hr />
                <div className="flex flex-col gap-1 py-6 text-zinc-800 sm:flex-row sm:gap-5">
                  <div className="sticky top-14 flex-1 bg-white pb-4">
                    <h1 className="hover:text-gold sticky top-14 flex w-fit cursor-pointer text-xl font-medium leading-6 sm:text-lg sm:leading-6">
                      Best Screenplay Written Directly for the Screen—based on
                      factual material or on story material not previously
                      published or produced
                    </h1>
                  </div>
                  <div className="flex flex-1 flex-col gap-3">
                    <Nominee
                      winner={false}
                      titles={["Maestro"]}
                      names={["Bradley Cooper"]}
                      roles={["Leonard Bernstein"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["Rustin"]}
                      names={["Colman Domingo"]}
                      roles={["Bayard Rustin"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["The Holdovers"]}
                      names={["Paul Giamatti"]}
                      roles={["Paul Hunham"]}
                    />
                    <Nominee
                      winner={true}
                      titles={["Oppenheimer"]}
                      names={["Cillian Murphy"]}
                      roles={["J. Robert Oppenheimer"]}
                    />
                    <Nominee
                      winner={false}
                      titles={["American Fiction"]}
                      names={["Jeffrey Wright"]}
                      roles={['Thelonius "Monk" Ellison']}
                    />
                  </div>
                </div>
                <hr />
              </TabPanel>
              <TabPanel>content 2</TabPanel>
            </TabPanels>
          </TabGroup>
        </div>
      </section>
    </div>
  );
}

function Card({
  category,
  title,
  names,
  title_first,
}: {
  category: string;
  title: string;
  names: string[];
  title_first: boolean;
}) {
  return (
    <div className="flex flex-col gap-2">
      <a
        className="text-xxs hover:text-gold w-fit max-w-full cursor-pointer truncate font-semibold text-zinc-800"
        title={category}
      >
        {category.toUpperCase()}
      </a>
      <div className="h-48 rounded-md border border-zinc-200 bg-white"></div>
      <div className="flex flex-col gap-1 font-medium text-zinc-800">
        <div className="text-sm leading-4 text-zinc-800">
          {title_first ? (
            <a className="hover:text-gold cursor-pointer italic underline decoration-zinc-200 underline-offset-2">
              {title}
            </a>
          ) : (
            names.map((n, i) => (
              <span key={i}>
                <a className="hover:text-gold cursor-pointer underline decoration-zinc-200 underline-offset-2">
                  {n}
                </a>
                {i != names.length - 1 && ", "}
              </span>
            ))
          )}
        </div>
        <div className="text-xs leading-[0.875rem] text-zinc-500">
          {title_first ? (
            names.map((n, i) => (
              <span key={i}>
                <a className="hover:text-gold cursor-pointer underline decoration-zinc-200 underline-offset-2">
                  {n}
                </a>
                {i != names.length - 1 && ", "}
              </span>
            ))
          ) : (
            <a className="hover:text-gold cursor-pointer italic underline decoration-zinc-200 underline-offset-2">
              {title}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function Nominee({
  winner,
  titles,
  names,
  roles,
}: {
  winner: boolean;
  titles: string[];
  names: string[];
  roles: string[];
}) {
  return (
    <div className="flex flex-row gap-2">
      <IconStarFilled
        className={`${winner ? "visible" : "invisible"} fill-gold mt-1 h-4 w-4`}
      />
      <div className="flex flex-col gap-1">
        <div className="text-base font-medium leading-5 text-zinc-800">
          {names.map((n, i) => (
            <span key={i}>
              <a className="hover:text-gold w-fit cursor-pointer underline decoration-zinc-300 underline-offset-2">
                {n}
              </a>
              {i != names.length - 1 && ", "}
            </span>
          ))}
        </div>

        <div className="text-sm font-normal leading-4 text-zinc-500">
          {roles.map((t, i) => (
            <span key={i}>
              <a className="w-fit">{t}</a>
              {i != names.length - 1 && ", "}
            </span>
          ))}
          ,&nbsp;
          {titles.map((t, i) => (
            <span key={i}>
              <a className="hover:text-gold w-fit cursor-pointer italic underline decoration-zinc-300 underline-offset-2">
                {t}
              </a>
              {i != names.length - 1 && ", "}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
