import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar
from urllib.parse import quote_plus
from typing import AsyncGenerator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from log import logger
from utils import get_env_var


class DatabaseConnection:
    _pools: dict[str, AsyncConnectionPool] = {}
    _pool_lock: asyncio.Lock | None = None

    _active_ctx: ContextVar = ContextVar("_active_ctx")

    def __init__(self, conninfo: str | None = None) -> None:
        if conninfo:
            self._conninfo = conninfo
            self._pool_min = 1
            self._pool_max = 3
            self._app_name = "pgwarden_collector"
        else:
            host = get_env_var("DB_HOST")
            port = get_env_var("DB_PORT")
            user = get_env_var("DB_USER")
            password = quote_plus(get_env_var("DB_PASSWORD"))
            dbname = get_env_var("DB_NAME")
            self._conninfo = (
                f"host={host} "
                f"port={port} "
                f"user={user} "
                f"password={password} "
                f"dbname={dbname}"
            )
            self._pool_min = 2
            self._pool_max = 10
            self._app_name = "pgwarden_metrics"

        self._conninfo += (
            f" options='-c statement_timeout=5000"
            f" -c lock_timeout=1000"
            f" -c application_name={self._app_name}'"
        )

    @classmethod
    async def _ensure_pool(cls, conninfo: str, min_size: int, max_size: int) -> AsyncConnectionPool:
        if conninfo in cls._pools:
            return cls._pools[conninfo]

        if cls._pool_lock is None:
            cls._pool_lock = asyncio.Lock()

        async with cls._pool_lock:
            if conninfo in cls._pools:
                return cls._pools[conninfo]

            pool = AsyncConnectionPool(
                conninfo=conninfo,
                min_size=min_size,
                max_size=max_size,
                max_waiting=30,
                max_lifetime=1800,
                max_idle=300,
                reconnect_timeout=30,
                kwargs={"row_factory": dict_row},
                open=False,
            )
            await pool.open(wait=True, timeout=10)
            cls._pools[conninfo] = pool
            await logger.info("Database", "Pool", f"Pool opened ({conninfo[:40]}...)")
            return pool

    @classmethod
    async def close_pool(cls, conninfo: str) -> None:
        pool = cls._pools.pop(conninfo, None)
        if pool:
            await pool.close()
            await logger.info("Database", "Pool", f"Pool closed ({conninfo[:40]}...)")

    @classmethod
    async def shutdown(cls) -> None:
        if not cls._pools:
            return
        await asyncio.gather(
            *[pool.close() for pool in cls._pools.values()],
            return_exceptions=True,
        )
        cls._pools.clear()
        await logger.info("Database", "Pool", "All pools closed")

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[psycopg.AsyncConnection, None]:
        pool = await self._ensure_pool(self._conninfo, self._pool_min, self._pool_max)
        conn = await pool.getconn()
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            await pool.putconn(conn)

    async def __aenter__(self) -> psycopg.AsyncConnection:
        ctx = self.acquire()
        conn = await ctx.__aenter__()
        self._active_ctx.set((ctx, conn))
        return conn

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ctx, _ = self._active_ctx.get()
        await ctx.__aexit__(exc_type, exc_val, exc_tb)