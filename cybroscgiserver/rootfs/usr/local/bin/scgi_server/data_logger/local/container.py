from asyncio import AbstractEventLoop
from typing import Optional

from lib.general.conditional_logger import get_logger
from lib.general.file_watcher import FileWatcher
from lib.general.paths import APP_DIR, CONFIG_FILE, \
    DATA_LOGGER_CONFIG_FILE
from lib.input_output.scgi.scgi_client import ScgiClient
from lib.services.alias_service import AliasService
from lib.services.cpu_intensive_task_runner import \
    CPUIntensiveTaskRunner
from data_logger.local.bootstrap import Bootstrap
from data_logger.local.config.config.config import Config
from data_logger.local.db.db import Db
from data_logger.local.db.repository import Repository
from data_logger.local.general.data_logger_activity_service import \
    DataLoggerActivityService
from data_logger.local.general.data_logger_service import DataLoggerService
from data_logger.local.general.logger_names import LoggerNames


class Container:
    def __init__(self,
                 config: Config,
                 main_loop: AbstractEventLoop,
                 program_file_name: str):
        """Construct container and set explicit dependencies.

        """
        self.config: Config = config
        self.main_loop: AbstractEventLoop = main_loop
        self.program_file_name: str = program_file_name

        self._db: Optional[Db] = None
        self._repository: Optional[Repository] = None
        self._alias_service: Optional[AliasService] = None
        self._data_logger_activity_service: Optional[
            DataLoggerActivityService
        ] = None
        self._scgi_client: Optional[ScgiClient] = None
        self._file_watcher: Optional[FileWatcher] = None
        self._data_logger_service: Optional[DataLoggerService] = None
        self._data_logger_bootstrap: Optional[Bootstrap] = None
        self._cpu_intensive_task_runner: Optional[
            CPUIntensiveTaskRunner
        ] = None

    @property
    def cpu_intensive_task_runner(self) -> CPUIntensiveTaskRunner:
        if self._cpu_intensive_task_runner is None:
            self._cpu_intensive_task_runner = CPUIntensiveTaskRunner()

        # noinspection PyTypeChecker
        return self._cpu_intensive_task_runner

    @property
    def db(self) -> Db:
        if self._db is None:
            self._db = Db(
                get_logger(LoggerNames.DB.name),
                self.config,
                self.main_loop
            )

        # noinspection PyTypeChecker
        return self._db

    @property
    def repository(self) -> Repository:
        if self._repository is None:
            self._repository = Repository(get_logger(LoggerNames.DB.name),
                                          self.db,
                                          self.config,
                                          self.cpu_intensive_task_runner,
                                          self.main_loop)

        # noinspection PyTypeChecker
        return self._repository

    @property
    def alias_service(self) -> AliasService:
        if self._alias_service is None:
            self._alias_service = AliasService(
                self.config.alias_config.aliases,
                self.config.alias_config.reversed
            )

        # noinspection PyTypeChecker
        return self._alias_service

    @property
    def file_watcher(self) -> FileWatcher:
        if self._file_watcher is None:
            log = get_logger(LoggerNames.FILE_WATCHER.name)

            self._file_watcher = FileWatcher(
                CONFIG_FILE, 
                lambda: FileWatcher.restart(log)
            )

        # noinspection PyTypeChecker
        return self._file_watcher

    @property
    def data_logger_activity_service(self) -> DataLoggerActivityService:
        if self._data_logger_activity_service is None:
            self._data_logger_activity_service = DataLoggerActivityService()

        # noinspection PyTypeChecker
        return self._data_logger_activity_service

    @property
    def scgi_client(self) -> ScgiClient:
        if self._scgi_client is None:
            self._scgi_client = ScgiClient(
                get_logger(LoggerNames.SCGI_CLIENT.name),
                self.config.scgi_config.server_address,
                self.config.scgi_config.scgi_port,
                self.config.scgi_config.tls_enabled,
                self.config.scgi_config.access_token
            )

        # noinspection PyTypeChecker
        return self._scgi_client

    @property
    def data_logger_service(self) -> DataLoggerService:
        if self._data_logger_service is None:
            self._data_logger_service = DataLoggerService(
                get_logger(LoggerNames.DATA_LOGGER.name),
                self.main_loop,
                self.repository,
                self.data_logger_activity_service,
                self.cpu_intensive_task_runner,
                self.scgi_client,
                self.alias_service,
                DATA_LOGGER_CONFIG_FILE
            )

        # noinspection PyTypeChecker
        return self._data_logger_service

    @property
    def data_logger_bootstrap(self) -> Bootstrap:
        if self._data_logger_bootstrap is None:
            self._data_logger_bootstrap = Bootstrap(
                get_logger(LoggerNames.DATA_LOGGER.name),
                self.db,
                self.file_watcher,
                self.data_logger_service,
                self.repository
            )

        # noinspection PyTypeChecker
        return self._data_logger_bootstrap
