import functools
import io
import zipfile
import zlib
from asyncio import get_running_loop

from scgi_server.local.general.errors import UnzipError


async def unzip(data: bytes) -> bytes:
    """Unpack downloaded ALC bytes without leaving temporary files behind."""
    blocking_task = functools.partial(_blocking_unzip, data)
    return await get_running_loop().run_in_executor(None, blocking_task)


def _blocking_unzip(data: bytes) -> bytes:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zipped_file:
            files = [item for item in zipped_file.infolist() if not item.is_dir()]
            return zipped_file.read(files[0])
    except (zipfile.BadZipFile, RuntimeError, IndexError, OSError, zlib.error) as e:
        raise UnzipError("Invalid allocation archive") from e
