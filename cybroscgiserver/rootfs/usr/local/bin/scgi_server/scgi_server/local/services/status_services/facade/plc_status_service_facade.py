import asyncio
from typing import Callable

from lib.input_output.scgi.r_response import RResponse
from scgi_server.local.services.rw_service.scgi_communication.rw_request \
    import RWRequest
from scgi_server.local.services.rw_service.subservices.plc_activity_service \
    .plc_activity import PlcActivity
from scgi_server.local.services.status_services.plc_status_service \
    .plc_status_service import PlcStatusService
from scgi_server.local.services.status_services.plc_status_service.single_plc_status_service import \
    SinglePlcStatusService


class PlcStatusServiceFacade:
    """
    Public interface for `PlcStatusService`
    """

    def __init__(self, plc_status_service: PlcStatusService):
        self._plc_status_service_manager: PlcStatusService = plc_status_service

    async def process(self,
                      nad: int,
                      requests: list[RWRequest]) -> list[RResponse]:
        coroutines = (self._process_request(nad, request) for
                      request in requests)
        responses = await asyncio.gather(*coroutines)
        return list(responses)

    async def _process_request(self,
                               nad: int,
                               request: RWRequest) -> RResponse:
        try:
            (value, description) = await self._get_value(
                nad, request.tag_name
            )
            return RResponse.create(
                request.name,
                request.tag_name,
                value,
                description
            )
        except KeyError:
            return RResponse.create(
                request.name,
                request.tag_name,
                code=RResponse.Code.UNKNOWN
            )

    async def _get_value(self, nad: int, tag_name: str) -> tuple[str, str]:
        plc_status_service = self._plc_status_service_manager[nad]
        return await (SinglePlcStatusServiceFacade(plc_status_service)
                      .get(tag_name))


class SinglePlcStatusServiceFacade:
    def __init__(self, single_plc_status_service: SinglePlcStatusService):
        self._single_plc_status_service = single_plc_status_service

        self._actions: dict[str, tuple[Callable[[], str], str]]
        self._actions = {
            "plc_status": (
                self._plc_program_status,
                "Controller status (ok, pgm missing, alc missing, offline, unknown)."
            ),
            "timestamp": (
                self._timestamp,
                "Time and date when program is sended."
            ),
            "ip_port": (
                self._ip_port,
                "IP address and UDP port of the controller."
            ),
            "response_time": (
                self._response_time,
                "Duration of last communication cycle in milliseconds."
            ),
            "bytes_transferred": (
                self._bytes_transferred,
                "Total number of bytes sent to and received from controller."
            ),
            "com_error_count": (
                self._com_error_count,
                "Total number of communication errors."
            ),
            "alc_file": (
                self._alc_file,
                "Complete allocation file in ASCII format."
            ),
        }

    async def get(self, tag_name: str) -> tuple[str, str]:
        action, description = self._actions[tag_name]
        value = await action()
        return value, description

    async def _plc_program_status(self) -> str:
        device_status = self._single_plc_status_service.device_status
        if device_status == PlcActivity.DeviceStatus.OFFLINE:
            return "offline"
        elif device_status == PlcActivity.DeviceStatus.NO_PROGRAM:
            return "pgm missing"
        elif device_status == PlcActivity.DeviceStatus.NO_ALCFILE:
            return "alc missing"
        elif device_status == PlcActivity.DeviceStatus.OK:
            return "ok"
        else:
            return "?"

    async def _timestamp(self) -> str:
        return str(self._single_plc_status_service.timestamp)

    async def _ip_port(self) -> str:
        ip_port = self._single_plc_status_service.ip_port
        if ip_port is not None:
            ip, port = ip_port
            if ip is not None:
                return f"{ip}:{port}"
        return "?"

    async def _response_time(self) -> str:
        response_time = self._single_plc_status_service.response_time
        return "?" if response_time is None \
            else f"{int(response_time.total_seconds() * 1000)}"

    async def _bytes_transferred(self) -> str:
        return str(self._single_plc_status_service.bytes_transferred)

    async def _com_error_count(self) -> str:
        return str(self._single_plc_status_service.communication_error_count)

    async def _alc_file(self) -> str:
        alc_file = await self._single_plc_status_service.get_alc_text()
        return "" if alc_file is None else f"\n{alc_file}\n"