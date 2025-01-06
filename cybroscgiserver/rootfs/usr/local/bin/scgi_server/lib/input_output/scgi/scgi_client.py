import asyncio
from typing import Optional

from lib.general.conditional_logger import ConditionalLogger
from lib.general.tls import create_client_tls_context
from lib.input_output.http.messages import \
    HttpRequestMessage, HttpResponseMessage


class ScgiClient:
    PAYLOAD_BYTES = 16 * 1024

    def __init__(self,
                 log: ConditionalLogger,
                 host: str,
                 port: int,
                 tls_enabled: bool,
                 access_token: Optional[str]):
        self._log: ConditionalLogger = log
        self._host: str = host
        self._port: int = port
        self._tls_enabled: bool = tls_enabled
        self._access_token: Optional[str] = access_token

    async def get(self, uri: str) -> str:
        """Connects to scgi server and gets requested data as xml.

        :param uri: Get variables describing which values to get in response
        xml (e.g. "c10010.test&c10020.abc").
        """
        reader, writer = await asyncio.open_connection(self._host, self._port)

        if self._tls_enabled:
            ssl_context = create_client_tls_context()
            await writer.start_tls(ssl_context)

        headers = {}
        if self._access_token:
            headers['Authorization'] = f'token {self._access_token}'

        request = HttpRequestMessage(
            method="GET",
            uri=f"/?{uri}",
            headers=headers
        )
        self._log.debug("req: " + request.serialize())

        writer.write(request.serialize().encode())
        await writer.drain()

        data = await reader.read(self.PAYLOAD_BYTES)
        self._log.debug(str(data))
        response = HttpResponseMessage.parse_response(data.decode())
        if response.status_code != 200:
            raise Exception(f"Request failed: {response.status_code} "
                            f"{response.status_message}")
        self._log.debug("resp: " + response.serialize())

        writer.close()
        await writer.wait_closed()

        return response.body
