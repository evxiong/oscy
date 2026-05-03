from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import pool
from .enums import AwardType
from .routers import (
    categories,
    ceremonies,
    entities_titles,
    nominations,
    search,
    version,
)
from .services.version import get_current_version

ALLOWED_ORIGIN_REGEX = (
    r"http://localhost:\d+|https://oscy.vercel.app|https://oscy.evanxiong.com"
)


@asynccontextmanager
async def lifespan(instance: FastAPI):
    await pool.open()
    yield
    await pool.close()


summary = """
API for querying Oscar nomination stats. Last updated: Apr. 23, 2026.
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

### Version

* Get the current version of data.
"""


app = FastAPI(
    title="oscy",
    summary=summary,
    description=description,
    version="0.1.2",
    license_info={
        "name": "MIT License",
        "url": "https://github.com/evxiong/oscy/blob/main/LICENSE",
    },
    lifespan=lifespan,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    redoc_url=None,
)


@app.middleware("http")
async def add_response_headers(request: Request, call_next):
    if request.url.path == "/version":
        response = await call_next(request)

        # do not allow caching of `/version` response
        response.headers["Cache-Control"] = "no-store"
    else:
        # return 304 Not Modified if If-None-Match request header matches
        # current version tag
        if_none_match = request.headers.get("If-None-Match")
        current_version = await get_current_version(AwardType.oscar)
        if if_none_match and current_version and if_none_match == current_version.tag:
            request_tag = request.query_params.get("v")
            if request_tag and request_tag == current_version.tag:
                cache_control = "public, max-age=31536000, immutable"
            else:
                cache_control = "public, max-age=86400, stale-while-revalidate=60"
            return Response(
                status_code=304,
                headers={
                    "Cache-Control": cache_control,
                    "ETag": current_version.tag,
                },
            )

        response = await call_next(request)

        if current_version:
            request_tag = request.query_params.get("v")
            if request_tag and request_tag == current_version.tag:
                # for versioned requests (with `v` query param) whose version
                # matches the current version, client/CDN cache can keep data
                # indefinitely
                response.headers["Cache-Control"] = (
                    "public, max-age=31536000, immutable"
                )
            else:
                # default behavior of non-versioned (or incorrectly versioned)
                # requests: client/CDN cache keeps for 1 day and serves stale
                # response for up to 1 minute while revalidating ETag in
                # background
                response.headers["Cache-Control"] = (
                    "public, max-age=86400, stale-while-revalidate=60"
                )

            response.headers["ETag"] = current_version.tag

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
)
app.include_router(nominations.router)
app.include_router(categories.router)
app.include_router(entities_titles.router)
app.include_router(ceremonies.router)
app.include_router(search.router)
app.include_router(version.router)
