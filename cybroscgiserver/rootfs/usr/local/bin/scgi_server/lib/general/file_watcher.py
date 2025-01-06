import os
import sys
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Callable, Dict, Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from lib.general.conditional_logger import ConditionalLogger


class FileWatcherError(Exception):
    pass


class FileWatcher:
    """Watches specified file for changes.

    On each change emits timestamp and file path as a tuple.
    """
    FILES = {}

    class EventHandler(FileSystemEventHandler):
        def on_any_event(self, event: FileSystemEvent) -> None:
            if event.is_directory or "~" in event.src_path:
                return
            super().on_any_event(event)

            FileWatcher.update_subject_with_file(
                Path(event.src_path.replace("\\", "/"))
            )

    def __init__(self,
                 loop: AbstractEventLoop,
                 log: ConditionalLogger,
                 monitored_path: Path,
                 monitored_files: Dict[Path, Callable[[], None]]):
        self._loop: AbstractEventLoop = loop
        self._log: ConditionalLogger = log
        self._monitored_path: Path = monitored_path
        self._monitored_files: Dict[Path, Callable[[], None]] = monitored_files

        FileWatcher.FILES = {
            str(filename): {
                'time': os.stat(filename).st_mtime,
                'callback': callback
            }
            for filename, callback in monitored_files.items()
        }

        self._observer: Optional[Observer] = None
        self._running = False

    def start(self) -> None:
        if self._running:
            raise FileWatcherError("Can't start cause it's already running")

        self._running = True

        self._observer = Observer()

        self._observer.schedule(
            self.EventHandler(),
            self._monitored_path.as_posix(),
            recursive=False
        )

        self._observer.start()

    def stop(self) -> None:
        if not self._running:
            raise FileWatcherError("Can't stop cause it's not running")

        self._running = False

        self._observer.stop()
        self._observer = None

    @classmethod
    def update_subject_with_file(cls, file: Path) -> None:
        filename = str(file)
        if filename in FileWatcher.FILES:
            new_time = os.stat(file).st_mtime
            old_time = FileWatcher.FILES[filename]['time']
            if old_time == 0.0:
                FileWatcher.FILES[filename]['time'] = new_time
            elif new_time != old_time:
                FileWatcher.FILES[filename]['time'] = new_time
                FileWatcher.FILES[filename]['callback']()

    @staticmethod
    def restart(log: ConditionalLogger) -> None:
        log.info(sys.argv[0] + " " + sys.executable)
        args = sys.argv[:]
        log.info('Re-spawning %s' % ' '.join(args))
        args.insert(0, sys.executable)
        if sys.platform == 'win32':
            args = ['"%s"' % arg for arg in args]

        os.chdir(os.getcwd())
        os.execv(sys.executable, args)
