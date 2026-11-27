from asyncio import AbstractEventLoop, Lock
from datetime import datetime
from itertools import chain
from typing import Optional, List, Dict
from zipfile import BadZipFile

from lib.general.conditional_logger import ConditionalLogger
from lib.general.misc import create_task_callback
from lib.input_output.scgi.r_response import RResponse
from lib.services.cpu_intensive_task_runner import \
    CPUIntensiveTaskRunner
from scgi_server.local.data_logger.data_logger_cache import DataLoggerCache
from scgi_server.local.general.errors import ExchangerTimeoutError, UnzipError
from scgi_server.local.general.unzip import unzip
from scgi_server.local.input_output.abus_stack.abus.abus_exchanger import \
    AbusExchanger
from scgi_server.local.services.plc_info_service.plc_info_service import \
    PlcInfoService
from scgi_server.local.services.rw_service.scgi_communication.rw_request \
    import RWRequest
from scgi_server.local.services.rw_service.subservices.plc_activity_service \
    .plc_activity_service import PlcActivityService
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .alc_service.alc_service import AlcService, AlcError
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .alc_service.var_info import VarInfo
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_cache.plc_cache import PlcCache
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_cache.plc_cache_facade import PlcCacheFacade
from scgi_server.local.services.rw_service.subservices \
    .plc_comm_service.plc_client_manager.plc_client.plc_client import PlcClient
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_client_manager.plc_client_manager import PlcClientManager
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_communicator import PlcCommunicator


class PlcCommService:
    def __init__(
        self,
        log: ConditionalLogger,
        plc_info_service: PlcInfoService,
        alc_service: AlcService,
        plc_activity_service: PlcActivityService,
        plc_client_manager: PlcClientManager,
        plc_cache: Optional[PlcCache],
        data_logger_cache: DataLoggerCache,
        cpu_intensive_task_runner: CPUIntensiveTaskRunner,
        only_user_variables: bool,
        loop: AbstractEventLoop
    ):
        self._log: ConditionalLogger = log
        self._plc_info_service: PlcInfoService = plc_info_service
        self._alc_service: AlcService = alc_service
        self._plc_activity_service: PlcActivityService = plc_activity_service
        self._plc_client_manager: PlcClientManager = plc_client_manager
        self._cache: Optional[PlcCache] = plc_cache
        self._data_logger_cache: DataLoggerCache = data_logger_cache
        self._cpu_intensive_task_runner: CPUIntensiveTaskRunner = (
            cpu_intensive_task_runner
        )
        self._only_user_variables: bool = only_user_variables
        self._loop: AbstractEventLoop = loop
        self._plc_locks: Dict[int, Lock] = {}
        self._transfer_dates: Dict[int, Optional[datetime]] = {}

    def set_exchanger(self, exchanger: AbusExchanger):
        self._plc_client_manager.set_exchanger(exchanger)

    async def process_rw_requests(self,
                                  nad: int,
                                  r_requests: List[RWRequest],
                                  w_requests: List[RWRequest],
                                  task_id: Optional[int]) -> List[RResponse]:
        # One complete operation per controller, including ALC loading and
        # cache updates. Other controllers can still proceed independently.
        async with self._get_plc_lock(nad):
            responses = await self._process_rw_requests(
                nad, r_requests, w_requests, task_id
            )
        self._log.debug(
            lambda: f"RW Results c{nad} - {len(responses)} responses"
        )
        return responses

    async def _process_rw_requests(self,
                                   nad: int,
                                   r_requests: List[RWRequest],
                                   w_requests: List[RWRequest],
                                   task_id: Optional[int],
                                   refresh: bool = False) -> List[RResponse]:
        plc_client = await self._plc_client_manager.get(nad)

        if plc_client is None or not plc_client.plc_info.has_ip:
            return [
                RResponse.create(
                    request.name,
                    request.tag_name,
                    request.value,
                    "",
                    False,
                    RResponse.Code.DEVICE_NOT_FOUND
                )
                for request in r_requests
            ]

        if self._cache is None:
            cache_facade = None
        else:
            cache_facade = PlcCacheFacade(self._log, self._cache[nad])

        plc_communicator = self._create_communicator(plc_client, cache_facade)

        if task_id is not None:
            if len(w_requests) > 0:
                # sanity check
                self._log.error(f"{len(w_requests)} write requests came from "
                                f"the data logger. They will be ignored.")
            return await plc_communicator.process_r_requests_for_data_logger(
                r_requests,
                task_id
            )

        if len(w_requests) > 0:
            return await plc_communicator.process_rw_requests(r_requests,
                                                              w_requests)

        if cache_facade is None:
            return await plc_communicator.process_rw_requests(r_requests,
                                                              [])
        else:
            cache_result = await cache_facade.read(r_requests)

            responses = list(chain(
                cache_result.fresh.values(),
                cache_result.stinky.values()
            ))
            postponable_requests = list(cache_result.stinky.keys())
            urgent_requests = list(cache_result.not_available)

        if refresh:
            # Another request may have refreshed these values while this
            # background operation waited for the controller lock.
            responses = list(cache_result.fresh.values())
            urgent_requests += postponable_requests
        elif len(postponable_requests) > 0:
            self._loop.create_task(
                self._refresh_cache(nad, postponable_requests)
            ).add_done_callback(create_task_callback(self._log))

        if len(urgent_requests) > 0:
            revision = cache_facade.revision
            new_responses = await plc_communicator.process_rw_requests(
                urgent_requests, []
            )
            if responses and revision != cache_facade.revision:
                # The header revealed a new program. Previously selected
                # cached values belong to the old program and must be dropped.
                return await self._process_rw_requests(
                    nad, r_requests, [], None, refresh=True
                )
            responses += new_responses

        return responses

    def _get_plc_lock(self, nad: int) -> Lock:
        if nad not in self._plc_locks:
            self._plc_locks[nad] = Lock()
        return self._plc_locks[nad]

    async def _refresh_cache(self,
                             nad: int,
                             requests: List[RWRequest]) -> None:
        async with self._get_plc_lock(nad):
            await self._process_rw_requests(nad, requests, [], None, refresh=True)

    def _create_communicator(self,
                             plc_client: PlcClient,
                             cache: Optional[PlcCacheFacade]) -> PlcCommunicator:
        return PlcCommunicator(
            self._log,
            plc_client,
            cache,
            self._plc_activity_service,
            self._get_alc,
            self._update_plc_client_datetime,
            self._update_plc_client_ip,
            self._cpu_intensive_task_runner,
            self._data_logger_cache,
            self._only_user_variables
        )

    async def _get_alc(self,
                       plc_client: PlcClient,
                       transfer_date: datetime) -> Dict[str, VarInfo]:
        nad = plc_client.plc_info.nad
        alc = await self._alc_service.load(nad, transfer_date)
        if alc is not None:
            return alc

        self._log.info(f"Loading alc for c{nad}, transfer_date={transfer_date}")
        return await self._fetch_alc_and_save(plc_client, transfer_date)

    async def _fetch_alc_and_save(self,
                                  plc_client: PlcClient,
                                  transfer_date: datetime) -> Dict[str, VarInfo]:
        try:
            alc_bytes_zipped = await plc_client.fetch_alc_file()
            alc_bytes = await unzip(alc_bytes_zipped)
        except (RuntimeError, BadZipFile, UnzipError, OSError) as e:
            raise AlcError("Can't read the controller allocation file") from e

        # A transfer may occur while the file is being downloaded. Do not
        # attach that file to a header read before the transfer.
        plc_head = await plc_client.read_plc_head()
        if not PlcCommunicator._is_plc_head_ok(plc_head):
            await self._update_plc_client_datetime(plc_client, None)
            raise PlcCommunicator.PlcHeadError()
        if plc_head.program_timestamp != transfer_date:
            await self._update_plc_client_datetime(
                plc_client, plc_head.program_timestamp
            )
            raise PlcCommunicator.PlcHeadError()

        return await self._alc_service.set_alc_bytes(
            plc_client.plc_info.nad, transfer_date, alc_bytes
        )

    async def _update_plc_client_datetime(
        self,
        plc_client: PlcClient,
        transfer_date: Optional[datetime]
    ) -> PlcClient:
        nad = plc_client.plc_info.nad
        if (nad not in self._transfer_dates or
                self._transfer_dates[nad] != transfer_date):
            self._transfer_dates[nad] = transfer_date
            self._alc_service.invalidate(nad, transfer_date)
            if self._cache is not None:
                self._cache.clear_plc(nad)
            self._data_logger_cache.clear_plc(nad)
            self._plc_activity_service.report_alc_transfer_date_used(nad, None)

        try:
            self._plc_info_service.get_plc_info(nad)
        except KeyError:
            # The periodic info cleaner may remove an entry during an await.
            self._plc_info_service.set_plc_info(plc_client.plc_info)
        if transfer_date is not None:
            self._plc_info_service.update_program_datetime(nad, transfer_date)
        return await self._plc_client_manager.get(nad)

    async def _update_plc_client_ip(
        self,
        plc_client: PlcClient
    ) -> Optional[PlcClient]:
        # deleting and requesting plc_info will implicitly trigger ip detection
        nad = plc_client.plc_info.nad
        try:
            await self._plc_info_service.remove_plc_info(nad)
        except KeyError:
            pass
        return await self._plc_client_manager.get(nad)

    async def get_alc(self, nad: int) -> Optional[Dict[str, VarInfo]]:
        """Obtain the current table for a socket event, even before an HTTP read."""
        async with self._get_plc_lock(nad):
            plc_client = await self._plc_client_manager.get(nad)
            if plc_client is None or not plc_client.plc_info.has_ip:
                return None

            communicator = self._create_communicator(plc_client, None)
            try:
                _, alc = await communicator.load_alc()
                return alc
            except (PlcCommunicator.PlcHeadError,
                    AlcError, ExchangerTimeoutError) as e:
                self._log.warning(f"Can't obtain alc for c{nad}: {e}")
                return None
