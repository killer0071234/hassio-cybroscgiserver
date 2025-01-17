from typing import List, Union

from scgi_server.local.general.errors import ExchangerTimeoutError
from scgi_server.local.services.rw_service.subservices.plc_comm_service.data_type import \
    DataType
from scgi_server.local.services.rw_service.subservices.plc_comm_service.plc_comm_service_request_processor import \
    PlcCommServiceRequestProcessor
from scgi_server.local.services.rw_service.subservices.plc_comm_service.plc_rw_requests \
    import PlcRWRequests


class PlcCommServiceWriteProcessor(PlcCommServiceRequestProcessor):
    async def _process_plc_rw_requests(self, requests: PlcRWRequests) -> None:
        self._log.debug(lambda: f"Write c{self._nad} begin - {requests}")

        one_b_addrs: List[int] = []
        one_b_values: List[int] = []
        two_b_addrs: List[int] = []
        two_b_values: List[Union[int, float, None]] = []
        four_b_addrs: List[int] = []
        four_b_values: List[Union[int, float, None]] = []
        four_b_types: List[DataType] = []

        for request in requests.one_byte:
            one_b_addrs.append(request.alc_data.addr)
            one_b_values.append(request.value)

        for request in requests.two_byte:
            two_b_addrs.append(request.alc_data.addr)
            two_b_values.append(request.value)

        for request in requests.four_byte:
            four_b_addrs.append(request.alc_data.addr)
            four_b_values.append(request.value)
            four_b_types.append(request.alc_data.data_type)

        try:
            await self._client.write_random_memory(
                one_b_addrs, two_b_addrs, four_b_addrs,
                one_b_values, two_b_values, four_b_values,
                four_b_types
            )
            self._log.debug(lambda: f"Write c{self._nad} succeeded")
        except ExchangerTimeoutError as e:
            self._log.debug(lambda: f"Write c{self._nad} failed with timeout",
                            exc_info=e)
            self._log.error(lambda: f"Write c{self._nad} failed with timeout: "
                                    f"{e}")
