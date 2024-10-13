from abc import ABC, abstractmethod

from lib.general.conditional_logger import ConditionalLogger
from lib.services.cpu_intensive_task_runner import \
    CPUIntensiveTaskRunner
from scgi_server.local.services.rw_service.scgi_communication.rw_request \
    import RWRequest
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .alc_service.var_info import VarInfo
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_client_manager.plc_client.plc_client import PlcClient
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_rw_request import AlcData, PlcRWRequest
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_rw_requests import PlcRWRequests


class PlcCommServiceRequestProcessor(ABC):
    def __init__(self,
                 log: ConditionalLogger,
                 client: PlcClient,
                 cpu_intensive_task_runner: CPUIntensiveTaskRunner):
        self._log: ConditionalLogger = log
        self._client: PlcClient = client
        self._cpu_intensive_task_runner: CPUIntensiveTaskRunner = (
            cpu_intensive_task_runner
        )

    @property
    def _nad(self) -> int:
        return self._client.plc_info.nad

    async def process(self,
                      requests: list[RWRequest],
                      alc: dict[str, VarInfo]):
        plc_rw_requests = self._create_plc_rw_requests(requests, alc)
        return await self._process_plc_rw_requests(plc_rw_requests)

    @abstractmethod
    async def _process_plc_rw_requests(self, requests):
        pass

    @classmethod
    def _create_plc_rw_requests(cls,
                                requests: list[RWRequest],
                                alc: dict[str, VarInfo]) -> PlcRWRequests:
        result = PlcRWRequests()

        for request in requests:
            plc_request = cls._create_plc_rw_request(request, alc)
            result.add(plc_request)

        return result

    @classmethod
    def _create_plc_rw_request(cls,
                               request: RWRequest,
                               alc: dict[str, VarInfo]) -> PlcRWRequest:
        var_name = request.tag_name

        try:
            var_info = alc[var_name]
            alc_data = AlcData(
                var_info.address,
                var_info.size,
                var_info.data_type,
                var_info.description
            )
            return PlcRWRequest.create(
                request.name,
                request.value,
                var_name,
                alc_data=alc_data,
                idx=request.idx
            )
        except KeyError:
            return PlcRWRequest.create(
                request.name,
                request.value,
                var_name,
                idx=request.idx
            )
