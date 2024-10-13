from datetime import timedelta
from typing import List

from scgi_server.constants import APP_VERSION
from scgi_server.local.input_output.abus_stack.udp.udp_activity_service \
    import UdpActivityService
from scgi_server.local.input_output.scgi.scgi_activity_service import \
    ScgiActivityService
from scgi_server.local.services.plc_info_service.plc_info_service import \
    PlcInfoService
from scgi_server.local.services.push_service.push_activity_service import \
    PushActivityService
from scgi_server.local.services.rw_service.subservices.plc_activity_service.plc_activity import \
    PlcActivity
from scgi_server.local.services.rw_service.subservices.plc_activity_service \
    .plc_activity_service import PlcActivityService
from scgi_server.local.services.status_services.plc_status_service \
    .plc_status_service import PlcStatusService


class SystemStatusService:
    def __init__(self,
                 plc_info_service: PlcInfoService,
                 push_activity_service: PushActivityService,
                 scgi_activity_service: ScgiActivityService,
                 plc_activity_service: PlcActivityService,
                 udp_activity_service: UdpActivityService,
                 plc_status_service: PlcStatusService,
                 cache_valid_period: timedelta,
                 cache_request_period: timedelta,
                 push_enabled: bool):
        self._plc_info_service = plc_info_service
        self._push_activity_service = push_activity_service
        self._scgi_activity_service = scgi_activity_service
        self._plc_activity_service = plc_activity_service
        self._udp_activity_service = udp_activity_service
        self._app_version = APP_VERSION
        self._plc_status_service = plc_status_service
        self._cache_valid_period: timedelta = cache_valid_period
        self._cache_request_period: timedelta = cache_request_period
        self._push_enabled: bool = push_enabled

    @property
    def scgi_status(self) -> str:
        return "active"

    @property
    def scgi_request_count(self) -> int:
        return self._scgi_activity_service.requests_received_count

    @property
    def server_version(self) -> str:
        return self._app_version

    @property
    def server_uptime(self) -> timedelta:
        return self._scgi_activity_service.server_uptime

    @property
    def cache_valid_period(self) -> timedelta:
        return self._cache_valid_period

    @property
    def cache_request_period(self) -> timedelta:
        return self._cache_request_period

    @property
    def is_push_port_active(self) -> bool:
        return self._push_enabled

    @property
    def push_plcs_count(self) -> int:
        return len(list(self._plc_info_service.get_push_plc_infos()))

    @property
    def failed_push_acknowledgments_count(self) -> int:
        return self._push_activity_service.failed_push_acknowledgments_count

    @property
    def successful_push_acknowledgments_count(self) -> int:
        return self._push_activity_service.successful_push_acknowledgments_count

    async def get_plcs(self) -> List[int]:
        return [plc_info.nad for plc_info in self._plc_info_service.get_plc_infos()]

    @property
    def push_plc_info_table(self):
        result = []
        for plc_info in self._plc_info_service.get_push_plc_infos():
            nad = plc_info.nad

            plc_status_service = self._plc_status_service[nad]
            plc_info = plc_status_service.plc_info

            status = plc_status_service.plc_status
            alc = plc_status_service.has_alc
            program = plc_info.program_datetime
            downloaded = "N/A"
            response = plc_status_service.response_time
            last_update_time = plc_info.last_update_time

            row = (
                plc_info.created.strftime("%d-%m-%y %H:%M:%S"),
                nad,
                f"{plc_info.ip}:{plc_info.port}",
                status,
                program,
                alc,
                downloaded,
                response,
                last_update_time
            )
            result.append(row)

        return result

    @property
    def udp_rx_count(self) -> int:
        return self._udp_activity_service.rx_count

    @property
    def udp_tx_count(self) -> int:
        return self._udp_activity_service.tx_count

    @property
    def plc_info_table(self):
        result = []
        for plc_info in self._plc_info_service.get_plc_infos():
            nad = plc_info.nad
            plc_activity = self._plc_activity_service[nad]
            initiated_exchanges_count = plc_activity.initiated_exchanges_count
            failed_exchanges_count = plc_activity.failed_exchanges_count
            last_failed_exchange_time = plc_activity.last_failed_exchange_time
            ip = plc_info.ip
            port = plc_info.port
            origin = plc_info.origin

            row = (
                nad,
                initiated_exchanges_count,
                failed_exchanges_count,
                None if last_failed_exchange_time is None
                else last_failed_exchange_time.strftime("%d-%m-%y %H:%M:%S"),
                ip,
                port,
                origin.value
            )
            result.append(row)

        return result