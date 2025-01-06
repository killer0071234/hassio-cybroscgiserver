from configparser import ConfigParser
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DebugLogConfig:
    @classmethod
    def create(
            cls,
            enabled: bool,
            log_to_file: bool,
            verbose_level: str,
            max_log_file_size_kb: int,
            max_log_backup_count: int
    ):
        return DebugLogConfig(
            enabled,
            log_to_file,
            verbose_level,
            max_log_file_size_kb,
            max_log_backup_count
        )

    enabled: bool
    log_to_file: bool
    verbose_level: str
    max_log_file_size_kb: int
    max_log_backup_count: int

    def props(self) -> Tuple[bool, bool, str, int, int]:
        return (
            self.enabled,
            self.log_to_file,
            self.verbose_level,
            self.max_log_file_size_kb,
            self.max_log_backup_count
        )

    @classmethod
    def load(cls, cp: ConfigParser, default: 'Config'):
        section = "DEBUGLOG"

        (
            enabled,
            log_to_file,
            verbose_level,
            max_log_file_size_kb,
            max_log_backup_count,
        ) = default.props()

        return cls.create(
            cp.getboolean(section, "enabled", fallback=enabled),
            cp.getboolean(section, "log_to_file", fallback=log_to_file),
            cp.get(section, "verbose_level", fallback=verbose_level),
            cp.getint(section, "max_file_size_kb",
                      fallback=max_log_file_size_kb),
            cp.getint(section, "max_backup_count",
                      fallback=max_log_backup_count),
        )
