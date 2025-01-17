from dataclasses import dataclass
from datetime import timedelta
from typing import Tuple


@dataclass(frozen=True)
class PushConfig:
    @classmethod
    def create(
            cls,
            enabled: bool,
            timeout_h: timedelta
    ):
        return cls(
            enabled,
            timedelta(hours=timeout_h)
        )

    enabled: bool
    timeout_h: timedelta

    def props(self) -> Tuple[bool, float]:
        return self.enabled, self.timeout_h.total_seconds() * 60 * 60

    @classmethod
    def load(cls, cp: 'ConfigParser', default: 'Config'):
        section = "PUSH"

        enabled, timeout_h = default.props()

        return cls.create(cp.getboolean(section, "enabled", fallback=enabled),
                          cp.getint(section, "timeout_h", fallback=timeout_h))
