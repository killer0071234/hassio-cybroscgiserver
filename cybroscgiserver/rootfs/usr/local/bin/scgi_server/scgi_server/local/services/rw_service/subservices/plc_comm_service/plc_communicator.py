from dataclasses import dataclass
from typing import Coroutine, Callable, Optional, Dict, List

from lib.general.conditional_logger import ConditionalLogger
from lib.input_output.scgi.r_response import RResponse
from lib.services.cpu_intensive_task_runner import \
    CPUIntensiveTaskRunner
from scgi_server.local.data_logger.data_logger_cache import DataLoggerCache
from scgi_server.local.general.errors import ExchangerTimeoutError
from scgi_server.local.services.plc_info_service.plc_info import PlcInfo
from scgi_server.local.services.rw_service.scgi_communication.rw_request \
    import RWRequest
from scgi_server.local.services.rw_service.subservices.plc_activity_service \
    .plc_activity_service import PlcActivityService
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .alc_service.var_info import VarInfo
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_cache.plc_cache_facade import PlcCacheFacade
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_client_manager.plc_client.plc_client import PlcClient
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_client_manager.plc_client.plc_head import PlcHead
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_client_manager.plc_client.status import PlcStatus, SystemStatus
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_comm_service_read_processor import PlcCommServiceReadProcessor
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_comm_service_write_processor import PlcCommServiceWriteProcessor


@dataclass
class PlcCommunicator:
    CYBRO_2_MAGIC = 31415
    CYBRO_3_MAGIC = 31416

    class PlcHeadError(Exception):
        def __init__(self, *args):
            super().__init__("plc head not ok", *args)

    def __init__(
        self,
        log: ConditionalLogger,
        plc_client: PlcClient,
        cache: Optional[PlcCacheFacade],
        plc_activity_service: PlcActivityService,
        handle_alc_request: Callable[
            [PlcClient, int],
            Coroutine[None, None, Optional[Dict[str, VarInfo]]]
        ],
        handle_plc_program_datetime_update,
        handle_plc_ip_update,
        cpu_intensive_task_runner: CPUIntensiveTaskRunner,
        data_logger_cache: DataLoggerCache,
        only_user_variables: bool
    ) -> None:
        self._log: ConditionalLogger = log
        self._plc_client: PlcClient = plc_client
        self._cache: Optional[PlcCacheFacade] = cache
        self._plc_activity_service: PlcActivityService = plc_activity_service
        self._get_alc = handle_alc_request
        self._update_plc_client_program_datetime = (
            handle_plc_program_datetime_update
        )
        self._update_plc_client_ip: Callable[
            [PlcClient], Coroutine[None, None, PlcClient]
        ] = handle_plc_ip_update
        self._cpu_intensive_task_runner: CPUIntensiveTaskRunner = (
            cpu_intensive_task_runner
        )
        self._data_logger_cache: DataLoggerCache = data_logger_cache
        self._only_user_variables: bool = only_user_variables

    async def process_rw_requests(self,
                                  r_requests: List[RWRequest],
                                  w_requests: List) -> List[RResponse]:
        if self._cache is not None:
            self._cache.start_futures(r_requests)

        responses = await self._process_rw_requests(r_requests, w_requests)

        if self._cache is not None:
            self._cache.write(responses)

        return responses

    async def _process_rw_requests(self,
                                   r_requests: List[RWRequest],
                                   w_requests: List[RWRequest]
                                   ) -> List[RResponse]:
        tries_taken = 0
        max_tries = \
            2 if self._plc_client.plc_info.origin != PlcInfo.Origin.STATIC \
            else 1

        while tries_taken < max_tries:
            try:
                if tries_taken > 0:
                    self._plc_client = await self._update_plc_client_ip(
                        self._plc_client
                    )
                if self._plc_client is not None:
                    return await self._read_write(r_requests, w_requests)
                else:
                    break
            except ExchangerTimeoutError:
                tries_taken += 1

        return self._create_r_responses_with_code(r_requests,
                                                  RResponse.Code.TIMEOUT)

    async def process_r_requests_for_data_logger(self,
                                                 r_requests: List[RWRequest],
                                                 task_id: int
                                                 ) -> List[RResponse]:
        tries_taken = 0
        max_tries = \
            2 if self._plc_client.plc_info.origin != PlcInfo.Origin.STATIC \
            else 1

        while tries_taken < max_tries:
            try:
                if tries_taken > 0:
                    self._plc_client = await self._update_plc_client_ip(
                        self._plc_client
                    )
                if self._plc_client is not None:
                    return await self._read_for_data_logger(r_requests,
                                                            task_id)
                else:
                    break
            except ExchangerTimeoutError:
                tries_taken += 1

        return self._create_r_responses_with_code(r_requests,
                                                  RResponse.Code.TIMEOUT)

    async def _read_for_data_logger(self,
                                    r_requests: List[RWRequest],
                                    task_id: int) -> List[RResponse]:
        try:
            crc = await self.plc_head_check()
        except self.PlcHeadError:
            return self._create_r_responses_with_code(
                r_requests,
                RResponse.Code.PLC_HEAD_ERROR
            )

        cached_item = await self._data_logger_cache.get(task_id, crc)

        if cached_item is not None:
            self._log.debug(f"cache found for (task: {task_id} crc: {crc})")

            self._plc_activity_service.report_alc_crc_used(
                self._plc_client.plc_info.nad,
                crc
            )

            return await PlcCommServiceReadProcessor(
                self._log,
                self._plc_client,
                self._cpu_intensive_task_runner,
                self._only_user_variables
            ).process_cache_item(cached_item)

        self._log.debug(f"cache not found for (task: {task_id} crc: {crc})")
        self._data_logger_cache.set_future(task_id, crc)

        try:
            alc = await self._get_alc(self._plc_client, crc)
            self._plc_activity_service.report_alc_crc_used(
                self._plc_client.plc_info.nad,
                None if alc is None else crc
            )

            if alc is None:
                self._data_logger_cache.cancel(task_id, crc)

                return self._create_r_responses_with_code(
                    r_requests,
                    RResponse.Code.DEVICE_NOT_FOUND
                )

            cache_item = None

            def on_cache_item_created(new_cache_item):
                nonlocal cache_item
                cache_item = new_cache_item

            result = await PlcCommServiceReadProcessor(
                self._log,
                self._plc_client,
                self._cpu_intensive_task_runner,
                self._only_user_variables,
                on_cache_item_created=on_cache_item_created
            ).process(r_requests, alc)

            if cache_item is not None:
                self._log.debug(
                    f"cache created for (task: {task_id} crc: {crc})"
                )
                self._data_logger_cache.set_future_result(task_id,
                                                          crc,
                                                          cache_item)
            else:
                self._data_logger_cache.cancel(task_id, crc)

            return result
        except BaseException as e:
            self._data_logger_cache.cancel(task_id, crc)
            raise e

    async def _read_write(self,
                          r_requests: List[RWRequest],
                          w_requests: List[RWRequest]) -> List[RResponse]:
        try:
            crc = await self.plc_head_check()
        except self.PlcHeadError:
            return self._create_r_responses_with_code(
                r_requests,
                RResponse.Code.PLC_HEAD_ERROR
            )

        try:
            alc = await self._get_alc(self._plc_client, crc)
        except RuntimeError:
            self._plc_activity_service.report_alc_crc_used(
                self._plc_client.plc_info.nad,
                None
            )
            return self._create_r_responses_with_code(
                r_requests,
                RResponse.Code.NO_ALC_ERROR
            )

        self._plc_activity_service.report_alc_crc_used(
            self._plc_client.plc_info.nad,
            None if alc is None else crc
        )

        if alc is None:
            return self._create_r_responses_with_code(
                r_requests,
                RResponse.Code.DEVICE_NOT_FOUND
            )

        if len(w_requests) > 0:
            await PlcCommServiceWriteProcessor(
                self._log,
                self._plc_client,
                self._cpu_intensive_task_runner,
                self._only_user_variables
            ).process(w_requests, alc)

        return await PlcCommServiceReadProcessor(
            self._log,
            self._plc_client,
            self._cpu_intensive_task_runner,
            self._only_user_variables
        ).process(r_requests, alc)

    async def plc_head_check(self) -> int:
        plc_head = await self._plc_client.read_plc_head()

        if not self._is_plc_head_ok(plc_head):
            raise self.PlcHeadError()

        last_program_datetime = self._plc_client.plc_info.program_datetime
        new_program_datetime = plc_head.program_timestamp

        if last_program_datetime is None:
            self._plc_client = await self._update_plc_client_program_datetime(
                self._plc_client,
                new_program_datetime
            )
        elif last_program_datetime != new_program_datetime:
            self._plc_client = await self._update_plc_client_program_datetime(
                self._plc_client,
                new_program_datetime
            )

            plc_head = await self._plc_client.read_plc_head()
            if not self._is_plc_head_ok(plc_head):
                raise self.PlcHeadError()

            status = await self._plc_client.read_status()
            if not self._is_status_ok(status):
                raise self.PlcHeadError()

        return plc_head.code_crc

    @classmethod
    def _is_status_ok(cls, status):
        return status.plc_status in (PlcStatus.RUN, PlcStatus.PAUSE) and \
               status.system_status == SystemStatus.KERNEL_ACTIVE

    @classmethod
    def _is_plc_head_ok(cls, plc_head: PlcHead) -> bool:
        return (cls._is_plc_program_ok(plc_head) and
                cls._could_plc_have_alc_file(plc_head))

    @classmethod
    def _is_plc_program_ok(cls, plc_head: PlcHead) -> bool:
        return (plc_head.empty == 0 and
                plc_head.magic in (cls.CYBRO_2_MAGIC, cls.CYBRO_3_MAGIC))

    @classmethod
    def _could_plc_have_alc_file(cls, plc_head: PlcHead) -> bool:
        return plc_head.file_system_addr > 0 and plc_head.file_count > 0

    @classmethod
    def _create_r_responses_with_code(cls,
                                      requests: List[RWRequest],
                                      code: RResponse.Code) -> List[RResponse]:
        return [
            RResponse.create(
                request.name,
                request.tag_name,
                request.value,
                "",
                False,
                code
            )
            for request in requests
        ]
