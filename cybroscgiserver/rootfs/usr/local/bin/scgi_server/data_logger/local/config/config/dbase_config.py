from configparser import ConfigParser
from dataclasses import dataclass
from typing import Tuple

from lib.config.ini_config_parser import IniConfigParser


@dataclass(frozen=True)
class DbaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    max_query_size: int

    def props(self) -> Tuple[str, int, str, str, str, int]:
        return (
            self.host,
            self.port,
            self.name,
            self.user,
            self.password,
            self.max_query_size,
        )

    @classmethod
    def load(cls, icp: IniConfigParser, default: 'DbaseConfig'):
        section = "DBASE"

        (
            host,
            port,
            name,
            user,
            password,
            max_query_size,
        ) = default.props()

        return cls(
            icp.get(section, "host", host),
            icp.get_int(section, "port", port),
            icp.get(section, "name", name),
            icp.get(section, "user", user),
            icp.get(section, "password", password),
            icp.get_int(section, "max_query_size", max_query_size),
        )
