import os
from dotenv import load_dotenv, find_dotenv
from psycopg_pool import AsyncConnectionPool


load_dotenv()
load_dotenv(find_dotenv(".config"))

pool = AsyncConnectionPool(
    conninfo=f"""
        dbname={os.getenv("PG_DBNAME")}
        user={os.getenv("PG_USER")}
        password={os.getenv("PG_PASSWORD")}
    """,
    open=False,
)
