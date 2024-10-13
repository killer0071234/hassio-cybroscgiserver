from asyncio import AbstractEventLoop

from scgi_server import CONFIG_FILE
from lib.general.conditional_logger import get_logger
from lib.general.file_watcher import FileWatcher
from lib.general.paths import APP_DIR
from lib.services.alias_service import AliasService
from lib.services.cpu_intensive_task_runner import \
    CPUIntensiveTaskRunner
from scgi_server.local.bootstrap import Bootstrap
from scgi_server.local.config.config.config import Config
from scgi_server.local.data_logger.data_logger_cache import DataLoggerCache
from scgi_server.local.general.logger_names import LoggerNames
from scgi_server.local.input_output.abus_stack.abus.abus_transceiver import \
    AbusTransceiver
from scgi_server.local.input_output.abus_stack.can_protocol.can_transceiver \
    import CanTransceiver
from scgi_server.local.input_output.abus_stack.can_protocol.iex_transceiver \
    import IexTransceiver
from scgi_server.local.input_output.abus_stack.router import Router
from scgi_server.local.input_output.abus_stack.udp.udp_activity_service \
    import UdpActivityService
from scgi_server.local.input_output.abus_stack.udp.udp_transceiver import \
    UdpTransceiver
from scgi_server.local.input_output.scgi.scgi_activity_service import \
    ScgiActivityService
from scgi_server.local.input_output.scgi.scgi_server import ScgiServer
from scgi_server.local.input_output.tcp.server import TCPServer
from scgi_server.local.services.plc_detection_service.plc_detection_service \
    import PlcDetectionService
from scgi_server.local.services.plc_info_service.plc_info_cleaner import \
    PlcInfoCleaner
from scgi_server.local.services.plc_info_service.plc_info_service import \
    PlcInfoService
from scgi_server.local.services.push_service.push_activity_service import \
    PushActivityService
from scgi_server.local.services.push_service.push_service import PushService
from scgi_server.local.services.rw_service.rw_service import RWService
from scgi_server.local.services.rw_service.subservices.plc_activity_service \
    .plc_activity_service import PlcActivityService
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .alc_service.alc_service import AlcService
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_cache.plc_cache import PlcCache
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_client_manager.plc_client_manager import PlcClientManager
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_comm_service import PlcCommService
from scgi_server.local.services.socket_service.socket_service import \
    SocketService
from scgi_server.local.services.status_services.facade \
    .plc_status_service_facade import PlcStatusServiceFacade
from scgi_server.local.services.status_services.facade \
    .system_status_service_facade import SystemStatusServiceFacade
from scgi_server.local.services.status_services.plc_status_service \
    .plc_status_service import PlcStatusService
from scgi_server.local.services.status_services.system_status_service import \
    SystemStatusService


class Container:
    def __init__(self,
                 config: Config,
                 main_loop: AbstractEventLoop,
                 communication_loop: AbstractEventLoop,
                 program_file_name: str):
        """Construct container and set explicit dependencies."""

        self.config: Config = config
        self.main_loop: AbstractEventLoop = main_loop
        self.communication_loop: AbstractEventLoop = communication_loop
        self.program_file_name: str = program_file_name

        self._alias_service: AliasService | None = None
        self._udp_activity_service: UdpActivityService | None = None
        self._plc_activity_service: PlcActivityService | None = None
        self._scgi_activity_service: ScgiActivityService | None = None
        self._push_activity_service: PushActivityService | None = None
        self._data_logger_cache: DataLoggerCache | None = None
        self._plc_info_service: PlcInfoService | None = None
        self._alc_service: AlcService | None = None
        self._system_status_service: SystemStatusService | None = None
        self._plc_status_service: PlcStatusService | None = None
        self._system_status_service_facade: (
                SystemStatusServiceFacade | None
        ) = None
        self._plc_status_service_facade: PlcStatusServiceFacade | None = None
        self._detection_service: PlcDetectionService | None = None
        self._push_service: PushService | None = None
        self._plc_client_manager: PlcClientManager | None = None
        self._plc_cache: PlcCache | None = None
        self._plc_communication_service: PlcCommService | None = None
        self._rw_service: RWService | None = None
        self._router: Router | None = None
        self._abus_transceiver: AbusTransceiver | None = None
        self._udp_transceiver: UdpTransceiver | None = None
        self._can_transceiver: CanTransceiver | None = None
        self._iex_transceiver: IexTransceiver | None = None
        self._scgi_server: ScgiServer | None = None
        self._tcp_server: TCPServer | None = None
        self._file_watcher: FileWatcher | None = None
        self._scgi_server_bootstrap: Bootstrap | None = None
        self._cpu_intensive_task_runner: CPUIntensiveTaskRunner | None = None
        self._plc_info_cleaner: PlcInfoCleaner | None = None
        self._socket_service: SocketService | None = None

    @property
    def cpu_intensive_task_runner(self) -> CPUIntensiveTaskRunner:
        if self._cpu_intensive_task_runner is None:
            self._cpu_intensive_task_runner = CPUIntensiveTaskRunner()

        return self._cpu_intensive_task_runner

    @property
    def alias_service(self) -> AliasService:
        if self._alias_service is None:
            self._alias_service = AliasService(
                get_logger(LoggerNames.ALIAS_SERVICE.name),
                self.config.alias_config.aliases,
                self.config.alias_config.reversed
            )

        return self._alias_service

    # region Activity
    @property
    def udp_activity_service(self) -> UdpActivityService:
        if self._udp_activity_service is None:
            self._udp_activity_service = UdpActivityService()

        return self._udp_activity_service

    @property
    def plc_activity_service(self) -> PlcActivityService:
        if self._plc_activity_service is None:
            self._plc_activity_service = PlcActivityService()

        return self._plc_activity_service

    @property
    def scgi_activity_service(self) -> ScgiActivityService:
        if self._scgi_activity_service is None:
            self._scgi_activity_service = ScgiActivityService()

        return self._scgi_activity_service

    @property
    def push_activity_service(self) -> PushActivityService:
        if self._push_activity_service is None:
            self._push_activity_service = PushActivityService()

        return self._push_activity_service

    @property
    def file_watcher(self) -> FileWatcher:
        if self._file_watcher is None:
            log = get_logger(LoggerNames.FILE_WATCHER.name)
            self._file_watcher = FileWatcher(
                self.main_loop,
                log,
                APP_DIR,
                {CONFIG_FILE: lambda: FileWatcher.restart(log)}
            )

        return self._file_watcher

    # endregion

    @property
    def data_logger_cache(self) -> DataLoggerCache:
        if self._data_logger_cache is None:
            self._data_logger_cache = DataLoggerCache(self.main_loop)

        return self._data_logger_cache

    # region Plc Info
    @property
    def plc_info_service(self) -> PlcInfoService:
        if self._plc_info_service is None:
            self._plc_info_service = PlcInfoService(
                get_logger(LoggerNames.PLC_INFO.name),
                self.main_loop,
                self.config.abus_config.password,
                self.config.push_config.timeout_h,
                self.config.static_plcs_config.static_plcs_configs
            )

        return self._plc_info_service

    # endregion

    @property
    def alc_service(self) -> AlcService:
        if self._alc_service is None:
            self._alc_service = AlcService(
                get_logger(LoggerNames.ALC.name),
                self.main_loop,
                self.config.locations_config.alc_dir
            )

        return self._alc_service

    # region Status
    @property
    def system_status_service(self) -> SystemStatusService:
        if self._system_status_service is None:
            self._system_status_service = SystemStatusService(
                self.plc_info_service,
                self.push_activity_service,
                self.scgi_activity_service,
                self.plc_activity_service,
                self.udp_activity_service,
                self.plc_status_service,
                self.config.cache_config.valid_period,
                self.config.cache_config.request_period,
                self.config.push_config.enabled
            )

        return self._system_status_service

    @property
    def plc_status_service(self) -> PlcStatusService:
        if self._plc_status_service is None:
            self._plc_status_service = PlcStatusService(
                self.plc_info_service,
                self.plc_activity_service,
                self.alc_service
            )

        return self._plc_status_service

    @property
    def system_status_service_facade(self) -> SystemStatusServiceFacade:
        if self._system_status_service_facade is None:
            self._system_status_service_facade = SystemStatusServiceFacade(
                self.system_status_service
            )

        return self._system_status_service_facade

    @property
    def plc_status_service_facade(self) -> PlcStatusServiceFacade:
        if self._plc_status_service_facade is None:
            self._plc_status_service_facade = PlcStatusServiceFacade(
                self.plc_status_service
            )

        return self._plc_status_service_facade

    # endregion

    @property
    def detection_service(self) -> PlcDetectionService:
        if self._detection_service is None:
            self._detection_service = PlcDetectionService(
                get_logger(LoggerNames.PLC_DETECT.name),
                self.plc_info_service,
                self.config.eth_config.enabled,
                self.config.eth_config.autodetect_enabled,
                self.config.eth_config.autodetect_address,
                self.config.can_config.enabled
            )

        return self._detection_service

    @property
    def push_service(self) -> PushService:
        if self._push_service is None:
            self._push_service = PushService(
                get_logger(LoggerNames.PUSH.name),
                self.main_loop,
                self.plc_info_service,
                self.plc_activity_service,
                self.push_activity_service
            )

        return self._push_service

    @property
    def plc_client_manager(self) -> PlcClientManager:
        if self._plc_client_manager is None:
            self._plc_client_manager = PlcClientManager(
                get_logger(LoggerNames.PLC_COMM.name),
                get_logger(LoggerNames.PLC_CLIENT.name),
                self.main_loop,
                self.plc_info_service,
                self.plc_activity_service,
                self.detection_service,
                self.cpu_intensive_task_runner
            )

        return self._plc_client_manager

    @property
    def plc_cache(self) -> PlcCache | None:
        if self.config.cache_config.valid_period == 0:
            self._plc_cache = None
            return self._plc_cache

        if self._plc_cache is None:
            self._plc_cache = PlcCache(
                self.main_loop,
                self.config.cache_config.cleanup_period_s,
                self.config.cache_config.request_period,
                self.config.cache_config.valid_period,
            )

        return self._plc_cache

    @property
    def plc_communication_service(self) -> PlcCommService:
        if self._plc_communication_service is None:
            self._plc_communication_service = PlcCommService(
                get_logger(LoggerNames.PLC_COMM.name),
                self.plc_info_service,
                self.alc_service,
                self.plc_activity_service,
                self.plc_client_manager,
                self.plc_cache,
                self.data_logger_cache,
                self.cpu_intensive_task_runner
            )

        return self._plc_communication_service

    @property
    def rw_service(self) -> RWService:
        if self._rw_service is None:
            self._rw_service = RWService(
                self.system_status_service_facade,
                self.plc_status_service_facade,
                self.plc_communication_service,
                self.cpu_intensive_task_runner
            )

        return self._rw_service

    @property
    def router(self) -> Router:
        if self._router is None:
            self._router = Router(
                get_logger(LoggerNames.ABUS.name),
                self.communication_loop,
                self.push_service,
                self.detection_service,
                self.rw_service,
                self.socket_service,
                self.config.push_config.enabled,
                self.config.abus_config.timeout_ms,
                self.config.abus_config.number_of_retries
            )

        return self._router

    @property
    def abus_transceiver(self) -> AbusTransceiver:
        if self._abus_transceiver is None:
            self._abus_transceiver = AbusTransceiver(
                get_logger(LoggerNames.ABUS.name),
                self.router,
                self.config.can_config.enabled,
                self.config.eth_config.enabled
            )

        return self._abus_transceiver

    @property
    def udp_transceiver(self) -> UdpTransceiver:
        if self._udp_transceiver is None:
            self._udp_transceiver = UdpTransceiver(
                get_logger(LoggerNames.UDP.name),
                self.main_loop,
                self.communication_loop,
                self.abus_transceiver,
                self.udp_activity_service,
                self.config.eth_config.bind_address,
                self.config.eth_config.port
            )

        return self._udp_transceiver

    @property
    def can_transceiver(self) -> CanTransceiver:
        if self._can_transceiver is None:
            self._can_transceiver = CanTransceiver(
                self.communication_loop,
                get_logger(LoggerNames.CAN.name),
                self.iex_transceiver,
                self.config.can_config.interface,
                self.config.can_config.channel,
                self.config.can_config.bitrate
            )

        return self._can_transceiver

    @property
    def iex_transceiver(self) -> IexTransceiver:
        if self._iex_transceiver is None:
            self._iex_transceiver = IexTransceiver(
                get_logger(LoggerNames.CAN.name),
                self.abus_transceiver
            )

        return self._iex_transceiver

    # region SCGI
    @property
    def scgi_server(self) -> ScgiServer:
        if self._scgi_server is None:
            self._scgi_server = ScgiServer(
                get_logger(LoggerNames.SCGI_SERVER.name),
                self.rw_service,
                self.scgi_activity_service,
                self.alias_service,
                self.config.scgi_config.reply_with_descriptions,
                self.config.scgi_config.access_token
            )

        return self._scgi_server

    @property
    def tcp_server(self) -> TCPServer:
        if self._tcp_server is None:
            self._tcp_server = TCPServer(
                get_logger(LoggerNames.TCP.name),
                self.main_loop,
                self.scgi_server,
                self.config.scgi_config.scgi_bind_address,
                self.config.scgi_config.scgi_port,
                self.config.scgi_config.tls_enabled,
                self.config.scgi_config.access_token
            )

        return self._tcp_server

    # endregion

    @property
    def plc_info_cleaner(self) -> PlcInfoCleaner:
        if self._plc_info_cleaner is None:
            self._plc_info_cleaner = PlcInfoCleaner(
                get_logger(LoggerNames.PLC_INFO.name),
                self.plc_info_service
            )

        return self._plc_info_cleaner

    @property
    def socket_service(self) -> SocketService:
        if self._socket_service is None:
            self._socket_service = SocketService(
                get_logger(LoggerNames.SOCKET.name),
                self.main_loop,
                self.alc_service,
                self.plc_communication_service,
                self.alias_service,
                self.tcp_server.send_to_clients,
                self.config.eth_config.sockets
            )

        return self._socket_service

    @property
    def scgi_server_bootstrap(self) -> Bootstrap:
        if self._scgi_server_bootstrap is None:
            self._scgi_server_bootstrap = Bootstrap(
                get_logger(),
                self.plc_info_service,
                self.plc_client_manager,
                self.alc_service,
                self.udp_transceiver,
                self.can_transceiver,
                self.tcp_server,
                self.plc_info_cleaner,
                self.file_watcher,
                self.config.eth_config.enabled,
                self.config.can_config.enabled
            )

        return self._scgi_server_bootstrap
