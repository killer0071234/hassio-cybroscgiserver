import asyncio
import calendar
import functools
import os
import re
import tempfile
from asyncio import AbstractEventLoop
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from lib.general.conditional_logger import ConditionalLogger
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .alc_service.alc_parser import AlcParser
from scgi_server.local.services.rw_service.subservices.plc_comm_service \
    .alc_service.var_info import VarInfo


class AlcError(Exception):
    pass


@dataclass(frozen=True)
class AlcEntry:
    transfer_date: datetime
    variables: Dict[str, VarInfo]


class AlcService:
    LEGACY_FILENAME_REGEX = re.compile(r"crc-\d+\.alc")
    ENCODING = "latin-1"

    def __init__(self,
                 log: ConditionalLogger,
                 loop: AbstractEventLoop,
                 alc_dir: Path):
        self._log: ConditionalLogger = log
        self._loop: AbstractEventLoop = loop
        self._alc_dir: Path = alc_dir
        self._alc_by_nad: Dict[int, AlcEntry] = {}

    async def initialize(self) -> None:
        # Tables are loaded on demand, after reading the controller header.
        await self._loop.run_in_executor(None, self._initialize_blocking)

    def _initialize_blocking(self) -> None:
        self._alc_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        for path in self._alc_dir.iterdir():
            if (path.is_file() and
                    self.LEGACY_FILENAME_REGEX.fullmatch(path.name)):
                try:
                    path.unlink()
                    self._log.info(f"Removed legacy alc file \"{path}\"")
                except OSError as e:
                    # Legacy files are never used, even if removal fails.
                    self._log.error(f"Can't remove legacy alc file "
                                    f"\"{path}\": {e}")

    def get(self,
            nad: int,
            transfer_date: datetime) -> Optional[Dict[str, VarInfo]]:
        entry = self._alc_by_nad.get(nad)
        if entry is not None and entry.transfer_date == transfer_date:
            return entry.variables
        return None

    def invalidate(self,
                   nad: int,
                   transfer_date: Optional[datetime] = None) -> None:
        entry = self._alc_by_nad.get(nad)
        if entry is not None and entry.transfer_date != transfer_date:
            del self._alc_by_nad[nad]

    async def load(self,
                   nad: int,
                   transfer_date: datetime) -> Optional[Dict[str, VarInfo]]:
        """Return a table only if it belongs to this controller and transfer.

        Calls for the same controller are serialized by PlcCommService.
        """
        alc = self.get(nad, transfer_date)
        if alc is not None:
            return alc

        self.invalidate(nad, transfer_date)
        data = await self._load_alc_bytes(nad, transfer_date)
        if data is None:
            return None

        try:
            alc = self._parse(data)
        except AlcError as e:
            self._log.error(f"Can't parse cached alc for c{nad}: {e}")
            return None

        self._alc_by_nad[nad] = AlcEntry(transfer_date, alc)
        return alc

    async def set_alc_bytes(self,
                            nad: int,
                            transfer_date: datetime,
                            data: bytes) -> Dict[str, VarInfo]:
        alc = self._parse(data)
        await self._save_alc_bytes(nad, transfer_date, data)
        self._alc_by_nad[nad] = AlcEntry(transfer_date, alc)
        self._log.info(f"Added alc for c{nad}, transfer_date={transfer_date}")
        return alc

    async def load_alc_text(self,
                            nad: int,
                            transfer_date: datetime) -> Optional[str]:
        data = await self._load_alc_bytes(nad, transfer_date)
        return None if data is None else data.decode(self.ENCODING)

    @classmethod
    def _parse(cls, data: bytes) -> Dict[str, VarInfo]:
        try:
            return AlcParser.parse(data.decode(cls.ENCODING))
        except (ValueError, AttributeError, TypeError) as e:
            raise AlcError("Invalid allocation table") from e

    async def _load_alc_bytes(self,
                              nad: int,
                              transfer_date: datetime) -> Optional[bytes]:
        blocking_task = functools.partial(self._load_alc_bytes_blocking,
                                          nad, transfer_date)
        return await self._loop.run_in_executor(None, blocking_task)

    def _load_alc_bytes_blocking(self,
                                 nad: int,
                                 transfer_date: datetime) -> Optional[bytes]:
        path = self._alc_dir.joinpath(f"c{nad}.alc")
        try:
            with path.open("rb") as f:
                # Read the timestamp and content from the same open file.
                if os.fstat(f.fileno()).st_mtime != self._to_mtime(transfer_date):
                    return None
                return f.read()
        except FileNotFoundError:
            return None
        except OSError as e:
            self._log.error(f"Can't load alc file \"{path}\": {e}")
            return None

    async def _save_alc_bytes(self,
                              nad: int,
                              transfer_date: datetime,
                              data: bytes) -> None:
        blocking_task = functools.partial(self._save_alc_bytes_blocking,
                                          nad, transfer_date, data)
        future = self._loop.run_in_executor(None, blocking_task)
        cancelled = False
        try:
            while True:
                try:
                    await asyncio.shield(future)
                    break
                except asyncio.CancelledError:
                    if future.cancelled():
                        raise
                    # Keep the controller lock until writing has finished,
                    # even if cancellation is requested more than once.
                    cancelled = True
        except OSError as e:
            if cancelled:
                raise asyncio.CancelledError() from e
            raise AlcError(f"Can't save alc for c{nad}: {e}") from e
        if cancelled:
            raise asyncio.CancelledError()

    def _save_alc_bytes_blocking(self,
                                 nad: int,
                                 transfer_date: datetime,
                                 data: bytes) -> None:
        path = self._alc_dir.joinpath(f"c{nad}.alc")
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=self._alc_dir, prefix=f".c{nad}-",
                suffix=".tmp", delete=False
            ) as f:
                temporary_path = Path(f.name)
                f.write(data)
                f.flush()
                os.fsync(f.fileno())

            timestamp = self._to_mtime(transfer_date)
            os.utime(temporary_path, (timestamp, timestamp))
            if temporary_path.stat().st_mtime != timestamp:
                raise OSError("Filesystem cannot preserve transfer_date")
            os.replace(temporary_path, path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    @staticmethod
    def _to_mtime(transfer_date: datetime) -> int:
        # The PLC date has no timezone. Encode its fields as UTC so that
        # server timezone and daylight-saving changes cannot affect the key.
        return calendar.timegm(transfer_date.timetuple())
