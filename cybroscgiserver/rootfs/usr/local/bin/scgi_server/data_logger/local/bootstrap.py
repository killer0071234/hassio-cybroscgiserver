from data_logger.local.db.db import Db
from data_logger.local.db.repository import Repository
from data_logger.local.general.data_logger_service import DataLoggerService
from lib.general.conditional_logger import ConditionalLogger
from lib.general.file_watcher import FileWatcher


class Bootstrap:
    def __init__(self,
                 log: ConditionalLogger,
                 db: Db,
                 file_watcher: FileWatcher,
                 data_logger_service: DataLoggerService,
                 repository: Repository):
        self._log: ConditionalLogger = log
        self._db: Db = db
        self._file_watcher: FileWatcher = file_watcher
        self._data_logger_service: DataLoggerService = data_logger_service
        self._repository: Repository = repository

    async def run(self) -> None:
        self._log.info('Connecting to database')
        await self._db.start()

        self._log.info("Initializing database")
        await self._repository.init()

        self._data_logger_service.start()

        self._file_watcher.start()
