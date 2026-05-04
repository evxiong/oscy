<h1 align="center">oscy</h1>

<div align="center">

_Open-source Oscars database and API, designed for querying nomination stats_

<!-- 🎭 _pronounced OS-kee, a portmanteau of Oscar and Emmy_ 🎭 -->

**Data last updated Apr. 30, 2026 (includes 98th Oscars results)**

[Website](https://oscy.evanxiong.com)&nbsp;&nbsp;·&nbsp;&nbsp;
[Usage](#usage)&nbsp;&nbsp;·&nbsp;&nbsp;
[API docs](https://oscy.evanxiong.com/api/docs)&nbsp;&nbsp;·&nbsp;&nbsp;
[Database docs](/DATABASE.md)

</div>

## Introduction

A Postgres database, API, and web app allowing you to query nominees, winners,
stats, and superlatives across all Academy Awards\*. Each nomination has been
matched to its corresponding IMDb ids, allowing you to extend the capabilities
of this database as needed (including with
[TMDB](https://developer.themoviedb.org/reference/find-by-id)).

> \* Primetime Emmy nominations will be added in the near future

See oscy in action at [oscy.evanxiong.com](https://oscy.evanxiong.com).

This database will be updated (at least) on an annual basis. Data has been
manually verified to the best of my ability, though there may be some
discrepancies or errors. See [What's in the database](#whats-in-the-database)
for more details about the nominations included in the database.

## In this repo

[`data/`](/data/)

- [`db.dump`](/data/db.dump): a `pg_dump` of the latest version of the database,
  allowing you to reconstruct the database locally
- [`oscars.csv`](/data/oscars.csv): a CSV file containing all joined Oscar
  nomination data

[`backend/db/`](/backend/db/)

- Python modules and scripts used to scrape data, construct the database, and
  update it; this code should NOT be used to copy the database -- see
  [Usage](#database-only)

[`backend/api/`](/backend/api/)

- Python API code

[`frontend/`](/frontend/)

- Next.js web app - an Oscars ceremony explorer, which also serves as an example
  of what you can do with the oscy API

## What's in the database

- Data includes nominations from all Academy Awards ceremonies (1929-present).
- Data only includes competitive categories and their predecessors (no honorary
  or technical awards). A full list of included categories can be found in
  [`backend/db/data/oscar_categories.yaml`](/backend/db/data/oscar_categories.yaml).
- Data has been manually verified to the best of my ability, though there may be
  some discrepancies or errors.

### How to query

For more information on how the database is structured and how to use it
(including example queries), see [DATABASE.md](/DATABASE.md).

### Data sources

- [Official Academy Awards database](https://awardsdatabase.oscars.org/)
- [IMDb](https://www.imdb.com/event/ev0000003/)

## API documentation

The API is designed to simplify the most common types of nomination queries, and
provide structured JSON for use in other applications. Complex or one-off
queries should be run directly against the database using SQL.

The API docs are located at
[oscy.evanxiong.com/api/docs](https://oscy.evanxiong.com/api/docs). They can
also be accessed at [localhost:8000/docs](http://localhost:8000/docs) when
running locally.

If you want to use the oscy API in your own project, you should self-host the
database and API, or host via a cloud provider. The API endpoints used by the
example docs and web app are not designed to handle large amounts of traffic.

## Usage

### Database only

**If you are only interested in the database** and you already have Postgres 13+
installed, download [`data/db.dump`](/data/db.dump) and run the following
commands to create a new database called `oscy` containing the data:

```shell
# Create new database called 'oscy'
createdb -U <username> oscy

# Load data into database
pg_restore -O -1 -U <username> -d oscy <path to db.dump>
```

### With Docker

This will create three containers: one for the Postgres database, one for the
API, and one for the Next.js frontend. The total size of the container images
will be ~950 MB.

#### Requirements

- [Docker Desktop](https://docs.docker.com/get-started/get-docker/)

#### Instructions

1. Clone the repo:

   ```shell
   git clone https://github.com/evxiong/oscy.git && cd oscy
   ```

2. Copy `.env.example` to a new file called `.env` and fill in the missing
   values.

3. Uncomment line 8 in [`frontend/next.config.ts`](/frontend/next.config.ts) so
   that `output` is set to `"standalone"`.

4. Build and run (make sure you are in the root project folder):

   ```shell
   docker compose up
   ```

It may take several minutes to build the images. All three components (database,
API, web app) should now be running and accessible from outside the containers:

- Postgres db at `localhost:5433` (**NOT 5432**)
- API at `localhost:8000`, docs are at `localhost:8000/docs`
- Web app at `localhost:3000`

### Without Docker

#### Requirements

- [Postgres 13+](https://www.postgresql.org/download/)
- [Python 3.12+](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/en/download)

#### Instructions

1. Clone the repo:

   ```shell
   git clone https://github.com/evxiong/oscy.git && cd oscy
   ```

2. Copy `.env.example` to a new file called `.env` and fill in the missing
   values.

3. Run the following commands to create the database:

   ```shell
   # Create new database called 'oscy'
   createdb -U <username> oscy

   # Load data into database
   pg_restore -O -1 -U <username> -d oscy data/db.dump
   ```

4. Run the following commands to set up the backend:

   ```shell
   cd backend

   # Create virtual env
   python -m venv .venv

   # Activate virtual env
   # (See https://docs.python.org/3/library/venv.html#how-venvs-work
   # for platform-specific instructions)
   source .venv/Scripts/activate

   # Install required packages
   pip install -r requirements.txt

   # Run API server
   fastapi run api/main.py

   cd ..
   ```

5. Run the following commands to set up the frontend:

   ```shell
   cd frontend

   # Install dependencies
   npm ci

   # Create optimized build
   # note: during the build process, the API server must be running
   npm run build

   # Run web app
   npm run start

   cd ..
   ```

All three components (database, API, web app) are now accessible:

- To connect to Postgres db: `psql -U <username> -d oscy`
- API accessible at `localhost:8000`
- Web app accessible at `localhost:3000`

## Future direction

Primetime Emmy nominations will be added in the near future, though it may take
longer due to the large number of categories and lack of centralized, accurate
data.

## Technologies used

Backend: Python (FastAPI, psycopg3), Postgres, Docker

Frontend: Typescript, Next.js, Tailwind CSS

Deployment: Vercel, Neon

## License

[MIT License](/LICENSE)
