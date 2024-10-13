from lib.general.conditional_logger import ConditionalLogger
from lib.general.file_watcher import FileWatcher
from scgi_server.local.input_output.abus_stack.can_protocol.can_transceiver \
    import CanTransceiver
from scgi_server.local.input_output.abus_stack.udp.udp_transceiver import \
    UdpTransceiver
from scgi_server.local.input_output.tcp.server import TCPServer
from scgi_server.local.services.plc_info_service.plc_info_cleaner import \
    PlcInfoCleaner
from scgi_server.local.services.plc_info_service.plc_info_service import \
    PlcInfoService
from scgi_server.local.services.rw_service.subservices.plc_comm_service. \
    alc_service.alc_service import AlcService
from scgi_server.local.services.rw_service.subservices.plc_comm_service. \
    plc_client_manager.plc_client_manager import PlcClientManager


class Bootstrap:
    """Starts and wires up all important parts of the scgi server system.

    """
    def __init__(
            self,
            log: ConditionalLogger,
            plc_info_service: PlcInfoService,
            plc_client_manager: PlcClientManager,
            alc_service: AlcService,
            udp_transceiver: UdpTransceiver,
            can_transceiver: CanTransceiver,
            tcp_server: TCPServer,
            plc_info_cleaner: PlcInfoCleaner,
            file_watcher: FileWatcher,
            eth_enabled: bool,
            can_enabled: bool
    ):
        self._log = log
        self._plc_info_service: PlcInfoService = plc_info_service
        self._plc_client_manager: PlcClientManager = plc_client_manager
        self._alc_service: AlcService = alc_service
        self._udp_transceiver: UdpTransceiver = udp_transceiver
        self._can_transceiver: CanTransceiver = can_transceiver
        self._tcp_server: TCPServer = tcp_server
        self._plc_info_cleaner: PlcInfoCleaner = plc_info_cleaner
        self._file_watcher = file_watcher
        self._eth_enabled: bool = eth_enabled
        self._can_enabled: bool = can_enabled

    async def run(self) -> None:
        self._plc_info_service.set_plc_client_manager(self._plc_client_manager)
        self._plc_info_service.load_static_plc_infos()

        self._log.info('Initializing alc service with alc files')
        await self._alc_service.initialize_with_alc_files()

        if self._eth_enabled:
            self._log.info('Initializing UDP communication')
            await self._udp_transceiver.start()
        else:
            self._log.info('Skipped UDP initialization')

        self._log.info('Initializing TCP communication')
        await self._tcp_server.start()

        if self._can_enabled:
            self._log.info('Initializing CAN communication')
            self._can_transceiver.start()
        else:
            self._log.info('Skipped CAN initialization')

        self._plc_info_cleaner.start()
        self._file_watcher.start()

