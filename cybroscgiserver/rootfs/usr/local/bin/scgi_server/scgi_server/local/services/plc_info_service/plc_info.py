from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


@dataclass
class PlcInfo:
    class Origin(Enum):
        STATIC = "STATIC",
        PUSH = "PUSH",
        AUTO = "AUTO"
        PROXY = 'PROXY'

    created: datetime
    origin: Origin
    nad: int
    ip: Optional[str]
    port: int
    password: Optional[int]
    program_datetime: Optional[datetime]
    last_update_time: datetime

    @property
    def has_ip(self) -> bool:
        return self.ip is not None

    @property
    def has_password(self) -> bool:
        return self.password is not None

    def props(self) -> tuple[datetime, Origin, int, str | None, int,
                             int | None, datetime]:
        return (
            self.created,
            self.origin,
            self.nad,
            self.ip,
            self.port,
            self.password,
            self.last_update_time
        )

    def __str__(self):
        ip_str = self.ip if self.has_ip else "?"

        result = f"{self.origin.name} c{self.nad} {ip_str}:{self.port}"

        if self.password is not None:
            result += f" password={self.password}"

        if self.program_datetime is not None:
            result += f" program={self.program_datetime}"

        return result
