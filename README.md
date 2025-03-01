<h1 align="center">oscy</h1>

<div align="center">

**Open-source Oscars database and API, designed for querying nomination stats**

🎭 _pronounced OS-kee, a portmanteau of Oscar and Emmy_ 🎭

**Data last updated Feb. 2025 (includes 97th Oscars nominations)**

[Website](https://oscy.vercel.app)&nbsp;&nbsp;·&nbsp;&nbsp;
[Running locally](#running-locally)&nbsp;&nbsp;·&nbsp;&nbsp;
[API docs](https://oscy.vercel.app/api/docs)&nbsp;&nbsp;·&nbsp;&nbsp;
[Database docs](https://github.com/evxiong/oscy/wiki/Database)

</div>

## Introduction

A Postgres database, API, and web app allowing you to query nominees, winners,
stats, and superlatives across all Academy Awards\*. Each nomination has been
matched to its corresponding IMDb ids, allowing you to extend the capabilities
of this database as needed (including with
[TMDB](https://developer.themoviedb.org/reference/find-by-id)).

> \* Primetime Emmy nominations will be added in the near future, hopefully ~
> Summer 2025.

See oscy in action at [oscy.vercel.app](https://oscy.vercel.app).

This database will be updated (at least) on an annual basis. Data has been
manually verified to the best of my ability, though there may be some
discrepancies or errors. See [What's in the database](#whats-in-the-database)
for more details about the nominations included in the database.

## What's in this repo

[`data/`](/data/)

- [`db.sql`](/data/db.sql): a `pg_dump` of the latest version of the database,
  allowing you to reconstruct the database locally
- [`oscars.csv`](/data/oscars.csv): a CSV file containing all joined Oscar
  nomination data

[`backend/db/`](/backend/db/)

- Python modules used to scrape data and construct the database; this code
  should NOT be used to copy the database -- see
  [Running locally](#database-only)

[`backend/api/`](/backend/api/)

- Python API code

[`frontend/`](/frontend/)

- Next.js web app - an Oscars ceremony explorer, which also serves as an example
  of what you can do with the oscy API.

## What's in the database

- Data includes nominations from all Academy Awards ceremonies (1929-present).
- Data only includes competitive categories and their predecessors (no honorary
  or technical awards). A full list of included categories can be found in
  [`backend/db/data/oscar_categories.yaml`](/backend/db/data/oscar_categories.yaml).
- Data has been manually verified to the best of my ability, though there may be
  some discrepancies or errors.

### How to query

For more information on how the database is structured and how to use it
(including example queries),
[visit the wiki page](https://github.com/evxiong/oscy/wiki/Database).

### Data sources

- [Official Academy Awards database](https://awardsdatabase.oscars.org/)
- [IMDb](https://www.imdb.com/event/ev0000003/)

## API documentation

The API is designed to simplify the most common types of nomination queries, and
provide structured JSON for use in other applications. Complex or one-off
queries should be run directly against the database using SQL.

The API docs are located at
[oscy.vercel.app/api/docs](https://oscy.vercel.app/api/docs). They can also be
accessed at [localhost:8000/docs](http://localhost:8000/docs) when running
locally.

If you want to use the oscy API in your own project, you should self-host the
database and API, or host via a cloud provider. The API endpoints used by the
example docs and web app are not designed to handle large amounts of traffic.

## Running locally

### Database only

**If you are only interested in the database** and you already have Postgres 13+
installed, download [`data/db.sql`](data/db.sql) and run the following commands
to create a new database called `oscy` containing the data:

```bash
$ createdb -U <username> oscy

$ psql -X -U <username> -d oscy -f <path to db.sql>
```

### With Docker

This will create three containers: one for the Postgres db, one for the API, and
one for the Next.js frontend. The total size of the container images will be
~1.1 GB.

#### Requirements

- [Docker Desktop](https://docs.docker.com/get-started/get-docker/)

#### Instructions

1. Run `git clone https://github.com/evxiong/oscy.git && cd oscy`

2. Copy `.env.example` to a new file called `.env` and fill in the missing
   values. `TMDB_API_KEY` is optional (used to fetch images in the web app).

3. Uncomment line 5 in [`frontend/next.config.ts`](/frontend/next.config.ts) so
   that `output` is set to `"standalone"`.

4. Run `docker compose up` from the root project folder.

It may take several minutes to build the images. All three components (database,
API, web app) should now be running:

- Postgres db is accessible at `localhost:5433` (**NOT 5432**)
- API is accessible at `localhost:8000`, docs are at `localhost:8000/docs`
- Web app is accessible at `localhost:3000`

### Without Docker

#### Requirements

- [Postgres 13+](https://www.postgresql.org/download/)
- [Python 3.12+](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/en/download)

#### Instructions

1. Run `git clone https://github.com/evxiong/oscy.git && cd oscy`
2. Copy `.env.example` to a new file called `.env` and fill in the missing
   values. `TMDB_API_KEY` is optional (used to fetch images in the web app).
3. Create database:

   ```bash
   $ createdb -U <username> oscy

   $ psql -X -U <username> -d oscy -f data/db.sql
   ```

4. Set up frontend: `cd frontend && npm ci && npm run build && cd ..`
5. Set up backend:
   1. Create venv: `cd backend && python -m venv .venv && cd .venv`
   2. [Activate venv](https://docs.python.org/3/library/venv.html#how-venvs-work):
      - Linux/macOS: `source bin/activate`
      - Windows: `source Scripts/activate`
      - `which python` should now return a path containing `.venv`
   3. `cd .. && pip install -r requirements.txt && cd ..`

All three components (database, API, web app) can now be run:

- To connect to Postgres db: `psql -U <username> -d oscy`
- To run API (accessible at `localhost:8000`):
  `cd backend && fastapi run api/main.py`
- To run web app (accessible at `localhost:3000`):
  `cd frontend && npm run start`

## Future direction

Primetime Emmy nominations will be added in the near future (hopefully around
Summer 2025), though it may take longer due to the large number of categories
and lack of centralized, accurate data.

## Technologies used

Backend: Python (FastAPI, psycopg3), Postgres, Docker

Frontend: Typescript, Next.js, Tailwind CSS

Deployment: Vercel, Neon

## License

[MIT License](/LICENSE)
