from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import categories, ceremonies, nominations, entities_titles, search
from .dependencies import pool

ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]


@asynccontextmanager
async def lifespan(instance: FastAPI):
    await pool.open()
    yield
    await pool.close()


summary = """
API for querying Oscar nomination stats. Last updated: Feb. 27, 2025.
"""

description = """
**Learn more about oscy at
[https://github.com/evxiong/oscy](https://github.com/evxiong/oscy).**

The oscy API is designed to abstract away most common types of nomination
queries, and provide structured responses. More complex queries should be [run
directly against the database](https://github.com/evxiong/oscy/wiki/Database).

### Nominations
* Get nominations and aggregate stats across multiple consecutive ceremonies,
with optional sorting/filtering.

### Categories

* Get the complete category hierarchy.
* Get nominations and stats across all ceremonies for a single category via oscy id.

### Entities and Titles

* Get nominations, stats, and rankings for a single entity via oscy id.
* Get nominations, stats, and rankings for a single title via oscy id.
* Get nominations, stats, and rankings for a single entity or title via IMDb id.

Entities can be people, companies, or countries.

### Ceremonies

* List all ceremonies.
* Get nominations and stats for a single ceremony via oscy id.

### Search

* Perform a paginated text search across titles, entities, categories, and
ceremonies, with optional filtering for titles and entities.
"""


app = FastAPI(
    title="oscy",
    summary=summary,
    description=description,
    version="1.0.0",
    license_info={
        "name": "MIT License",
        "url": "https://github.com/evxiong/oscy/blob/main/LICENSE",
    },
    lifespan=lifespan,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
)
app.include_router(nominations.router)
app.include_router(categories.router)
app.include_router(entities_titles.router)
app.include_router(ceremonies.router)
app.include_router(search.router)
