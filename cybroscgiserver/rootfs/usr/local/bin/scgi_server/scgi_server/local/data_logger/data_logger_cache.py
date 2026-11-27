from asyncio import AbstractEventLoop
from datetime import datetime
from typing import Any, Optional, Dict, Tuple

from scgi_server.local.general.async_cache import AsyncCache


class DataLoggerCache:
    """Prepared logger requests for each controller's current program."""

    def __init__(self, loop: AbstractEventLoop):
        self._loop: AbstractEventLoop = loop
        self._plc_caches: Dict[int, Tuple[datetime, AsyncCache]] = {}

    def __bool__(self) -> bool:
        return bool(self._plc_caches)

    async def get(self,
                  task_id: int,
                  nad: int,
                  transfer_date: datetime,
                  default: Optional[Any] = None) -> Optional[Any]:
        entry = self._plc_caches.get(nad)
        if entry is None or entry[0] != transfer_date:
            return default
        return await entry[1].get(task_id, default)

    def set_future(self,
                   task_id: int,
                   nad: int,
                   transfer_date: datetime) -> None:
        entry = self._plc_caches.get(nad)
        if entry is None or entry[0] != transfer_date:
            self.clear_plc(nad)
            entry = transfer_date, AsyncCache(self._loop)
            self._plc_caches[nad] = entry
        entry[1].set_future(task_id)

    def set_future_result(self,
                          task_id: int,
                          nad: int,
                          transfer_date: datetime,
                          value: Any) -> None:
        entry = self._plc_caches.get(nad)
        if entry is not None and entry[0] == transfer_date:
            entry[1].set_future_result(task_id, value)

    def cancel(self,
               task_id: int,
               nad: int,
               transfer_date: datetime) -> None:
        entry = self._plc_caches.get(nad)
        if entry is not None and entry[0] == transfer_date:
            entry[1].cancel(task_id)
            if not entry[1]:
                del self._plc_caches[nad]

    def clear_plc(self, nad: int) -> None:
        entry = self._plc_caches.pop(nad, None)
        if entry is not None:
            entry[1].clear()

    def clear(self) -> None:
        for nad in list(self._plc_caches):
            self.clear_plc(nad)
