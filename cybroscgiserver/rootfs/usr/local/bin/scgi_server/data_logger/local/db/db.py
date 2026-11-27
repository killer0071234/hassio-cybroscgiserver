from asyncio import AbstractEventLoop
from typing import Any, Optional

import aiomysql
from aiomysql import DatabaseError, Pool, Connection, Cursor

from data_logger.local.config.config.config import Config
from data_logger.local.config.config.dbase_config import DbaseConfig
from data_logger.local.general.errors import DataLoggerError
from lib.general.conditional_logger import ConditionalLogger


class Db:
    def __init__(self,
                 log: ConditionalLogger,
                 config: Config,
                 loop: AbstractEventLoop):
        self._log: ConditionalLogger = log
        self._config: DbaseConfig  = config.dbase_config
        self._pool: Optional[Pool] = None
        self._loop: AbstractEventLoop = loop

    async def start(self):
        try:
            self._pool = await aiomysql.create_pool(
                host=self._config.host,
                port=self._config.port,
                user=self._config.user,
                password=self._config.password,
                db=self._config.name,
                loop=self._loop,
                autocommit=True
            )

            async with self._pool.acquire() as conn:
                self._log.info(lambda: f"Connected to database "
                                       f"{conn.host}:{conn.port}/{conn.db}")
        except DatabaseError as e:
            self._log.critical("Couldn't connect to database", exc_info=e)
            raise DataLoggerError() from e

    async def execute_query(self, query: str, args: Optional[Any] = None):
        self._log.debug(lambda: f"{query[:100]}...")

        conn: Connection
        async with self._pool.acquire() as conn:
            cursor: Cursor
            async with conn.cursor() as cursor:
                await cursor.execute(query, args)
                result = await cursor.fetchall()
                return result
