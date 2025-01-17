from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Tuple, Union

from lib.config.errors import InvalidPassword


@dataclass(frozen=True)
class AbusConfig:
    @classmethod
    def create(cls,
               timeout_ms: timedelta,
               number_of_retries: int,
               password: Union[int, str]):
        try:
            password = None if password == "" else int(password)
        except ValueError:
            raise InvalidPassword(password)

        return cls(
            timedelta(milliseconds=timeout_ms),
            number_of_retries,
            password,
        )

    timeout_ms: timedelta
    number_of_retries: int
    password: Optional[int]

    def props(self) -> Tuple[float, int, str]:
        return (
            self.timeout_ms.total_seconds() * 1000,
            self.number_of_retries,
            "" if self.password is None else str(self.password),
        )

    @classmethod
    def load(cls, cp: 'ConfigParser', default: 'Config'):
        section = "ABUS"

        (
            timeout_ms,
            number_of_retries,
            password,
        ) = default.props()

        return cls.create(
            cp.getint(section, "timeout_ms", fallback=timeout_ms),
            cp.getint(section, "number_of_retries",
                      fallback=number_of_retries),
            cp.get(section, "password", fallback=password),
        )
