import asyncio
from datetime import datetime, timezone
from typing import Callable, Coroutine, Any

from psycopg.rows import dict_row

from collector.models import CollectorState, CollectorStatus
from database import DatabaseConnection, load_storage_query
from log import logger


_SELECT_COMMANDS   = load_storage_query(schema="collector", table="command", query_type="SELECT", query_name="pending")
_UPDATE_EXECUTED   = load_storage_query(schema="collector", table="command", query_type="UPDATE", query_name="executed")
_UPSERT_CONFIG     = load_storage_query(schema="collector", table="config",  query_type="INSERT", query_name="on_conflict")
_UPDATE_CONFIG     = load_storage_query(schema="collector", table="config",  query_type="UPDATE", query_name="success")

class Scheduler:
    COMMAND_POLL_INTERVAL = 5.0

    def __init__(self, metrics_db: DatabaseConnection) -> None:
        self._collectors: dict[str, CollectorState] = {}
        self._metrics_db = metrics_db
        self._running    = False

    def register(
        self,
        name:     str,
        fn:       Callable[[], Coroutine[Any, Any, None]],
        interval: float,
    ) -> None:
        if name in self._collectors:
            raise ValueError(f"Collector '{name}' is already registered")

        self._collectors[name] = CollectorState(name=name, interval=interval, fn=fn)

    async def start(self) -> None:
        self._running = True
        await self._sync_config_to_db()

        for state in self._collectors.values():
            self._spawn(state)

        asyncio.create_task(self._command_poller(), name="scheduler:command_poller")

        await logger.info("Scheduler", "start", f"{len(self._collectors)} collector(s) started")

    async def stop(self) -> None:
        self._running = False

        await asyncio.gather(
            *[self._cancel(state) for state in self._collectors.values()],
            return_exceptions=True,
        )

        await logger.info("Scheduler", "stop", "All collectors stopped")

    async def __aenter__(self) -> "Scheduler":
        await self.start()
        return self

    async def __aexit__(self, *_) -> None:
        await self.stop()

    async def pause(self, name: str) -> None:
        state = self._get(name)
        state._paused.clear()
        state.status = CollectorStatus.PAUSED
        await self._update_config(state)
        await logger.info("Scheduler", name, "Paused")

    async def resume(self, name: str) -> None:
        state = self._get(name)
        state._paused.set()
        if state.status == CollectorStatus.PAUSED:
            state.status = CollectorStatus.IDLE
        await self._update_config(state)
        await logger.info("Scheduler", name, "Resumed")

    async def force_run(self, name: str) -> None:
        state = self._get(name)
        if state.status == CollectorStatus.PAUSED:
            await logger.info("Scheduler", name, "Paused — skipping force run")
            return
        state._force.set()
        await logger.info("Scheduler", name, "Force run triggered")

    async def set_interval(self, name: str, interval: float) -> None:
        state = self._get(name)
        state.interval = interval
        state._force.set()
        await self._update_config(state)
        await logger.info("Scheduler", name, f"Interval set to {interval}s")

    async def _command_poller(self) -> None:
        await logger.info("Scheduler", "command_poller", "Started")

        while self._running:
            try:
                await self._process_pending_commands()
            except Exception as error:
                await logger.error("Scheduler", "command_poller", f"Error: {error}")
                raise error

            await asyncio.sleep(self.COMMAND_POLL_INTERVAL)

    async def _process_pending_commands(self) -> None:
        async with DatabaseConnection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(_SELECT_COMMANDS)
                commands = await cur.fetchall()

                for cmd in commands:
                    error = await self._dispatch(cmd["collector"], cmd["command"], cmd["payload"])

                    await cur.execute(_UPDATE_EXECUTED, {"id": cmd["id"], "error": error})

            await conn.commit()

    async def _dispatch(
        self,
        collector: str,
        command:   str,
        payload:   dict | None,
    ) -> str | None:
        try:
            if collector not in self._collectors:
                return f"Collector '{collector}' not found"

            if command == "pause":
                await self.pause(collector)

            elif command == "resume":
                await self.resume(collector)

            elif command == "force_run":
                await self.force_run(collector)

            elif command == "set_interval":
                interval = (payload or {}).get("interval")
                if not isinstance(interval, (int, float)) or interval <= 0:
                    return "set_interval requires payload {\"interval\": <positive number>}"
                await self.set_interval(collector, float(interval))

            else:
                return f"Unknown command '{command}'"

            return None

        except Exception as error:
            return str(error)

    async def _sync_config_to_db(self) -> None:
        async with self._metrics_db as conn:
            async with conn.cursor() as cur:
                for state in self._collectors.values():
                    await cur.execute(
                        _UPSERT_CONFIG,
                        {"name": state.name, "interval": state.interval},
                    )
            await conn.commit()

    async def _update_config(self, state: CollectorState) -> None:
        async with self._metrics_db as conn:
            async with conn.cursor() as cur:
                await cur.execute(_UPDATE_CONFIG, {
                    "name":        state.name,
                    "interval":    state.interval,
                    "is_paused":   not state._paused.is_set(),
                    "status":      state.status,
                    "last_run_at": state.last_run_at,
                    "last_error":  state.last_error,
                    "run_count":   state.run_count,
                    "error_count": state.error_count,
                })
            await conn.commit()

    def _spawn(self, state: CollectorState) -> None:
        state._task = asyncio.create_task(
            self._loop(state),
            name=f"collector:{state.name}",
        )

    async def _loop(self, state: CollectorState) -> None:
        while True:
            await state._paused.wait()

            try:
                await asyncio.wait_for(state._force.wait(), timeout=state.interval)
                state._force.clear()
            except asyncio.TimeoutError:
                pass

            if not state._paused.is_set():
                continue

            await self._run_once(state)

    async def _run_once(self, state: CollectorState) -> None:
        state.status = CollectorStatus.RUNNING
        await self._update_config(state)

        try:
            await state.fn()
            state.run_count  += 1
            state.last_run_at = datetime.now(tz=timezone.utc)
            state.last_error  = None
            state.status      = CollectorStatus.IDLE

        except asyncio.CancelledError:
            raise

        except Exception as error:
            state.error_count += 1
            state.last_error   = str(error)
            state.status       = CollectorStatus.ERROR
            await logger.error("Scheduler", state.name, f"Failed: {error}")

        finally:
            await self._update_config(state)

    async def _cancel(self, state: CollectorState) -> None:
        if state._task and not state._task.done():
            state._task.cancel()
            try:
                await state._task
            except asyncio.CancelledError:
                pass

    def _get(self, name: str) -> CollectorState:
        if name not in self._collectors:
            raise KeyError(f"Collector '{name}' not found")
        return self._collectors[name]