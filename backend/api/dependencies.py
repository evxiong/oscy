import asyncio
import os
import psycopg
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool

load_dotenv(override=True)

try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except:
    pass

conninfo = f"""
    host={os.getenv("PG_HOST")}
    port={os.getenv("PG_PORT")}
    dbname={os.getenv("PG_DBNAME")}
    user={os.getenv("PG_USER")}
    password={os.getenv("PG_PASSWORD")}
    sslmode={os.getenv("PG_SSLMODE")}
"""

pool = AsyncConnectionPool(conninfo, open=False)


@asynccontextmanager
async def connect():
    """Context manager that yields async db connection."""
    if (
        os.getenv("VERCEL_ENV") == "production"
        or os.getenv("VERCEL_ENV") == "preview"
        or os.getenv("PG_SSLMODE") == "require"
    ):
        async with await psycopg.AsyncConnection.connect(conninfo) as aconn:
            print("Creating normal connection")
            yield aconn
    else:
        try:
            async with pool.connection() as con:
                print("Accessing connection pool")
                yield con
        except:
            async with await psycopg.AsyncConnection.connect(conninfo) as aconn:
                print("Creating normal connection")
                yield aconn
