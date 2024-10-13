from asyncio import AbstractEventLoop
from datetime import timedelta

from rx import timer
from rx.scheduler.eventloop import AsyncIOScheduler

from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .plc_cache.single_plc_cache import SinglePlcCache


class PlcCache:
    def __init__(self,
                 loop: AbstractEventLoop,
                 cleanup_period: timedelta,
                 request_period: timedelta,
                 valid_period: timedelta):
        self._loop: AbstractEventLoop = loop
        self._plc_caches: dict[int, SinglePlcCache] = {}
        self._request_period: timedelta = request_period
        self._valid_period: timedelta = valid_period

        cleanup_period_s = cleanup_period.total_seconds()

        if cleanup_period_s != 0:
            timer(
                cleanup_period_s,
                cleanup_period_s,
                AsyncIOScheduler(loop)
            ).subscribe(lambda _: self._cleanup())

    def __getitem__(self, nad: int) -> SinglePlcCache:
        try:
            return self._plc_caches[nad]
        except KeyError:
            result = SinglePlcCache(
                self._loop,
                self._request_period,
                self._valid_period
            )
            self._plc_caches[nad] = result
            return result

    def _cleanup(self) -> None:
        for nad in self._plc_caches:
            self._plc_caches[nad].cleanup()
