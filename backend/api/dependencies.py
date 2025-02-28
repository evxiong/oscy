import asyncio
import os
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool


load_dotenv()

try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except:
    pass

pool = AsyncConnectionPool(
    conninfo=f"""
        host={os.getenv("PG_HOST")}
        port={os.getenv("PG_PORT")}
        dbname={os.getenv("PG_DBNAME")}
        user={os.getenv("PG_USER")}
        password={os.getenv("PG_PASSWORD")}
    """,
    open=False,
)
