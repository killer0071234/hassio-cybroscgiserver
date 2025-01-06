from configparser import ConfigParser
from dataclasses import dataclass
from enum import Enum
from typing import NewType, Dict, List, Tuple

from lib.config.config.util.ip_resolver import \
    resolve_broadcast_address
from lib.config.config.util.linesep import split_lines


class SocketDataType(Enum):
    BIT = 0
    UINT = 1
    LONG = 2


SocketsType = NewType('SocketsType',
                      Dict[int, Dict[SocketDataType, List[str]]])


@dataclass(frozen=True)
class EthConfig:
    @classmethod
    def create(
            cls,
            enabled: bool,
            bind_address: str,
            port: int,
            autodetect_enabled: bool,
            autodetect_address: str,
            sockets: SocketsType
    ):

        return EthConfig(
            enabled,
            bind_address,
            port,
            autodetect_enabled,
            autodetect_address,
            sockets
        )

    enabled: bool
    bind_address: str
    port: int
    autodetect_enabled: bool
    autodetect_address: str
    sockets: SocketsType

    def props(self) -> Tuple[bool, str, int, bool, str, SocketsType]:
        return (
            self.enabled,
            self.bind_address,
            self.port,
            self.autodetect_enabled,
            self.autodetect_address,
            self.sockets
        )

    @classmethod
    def load(cls, cp: ConfigParser, default: 'Config'):
        section = "ETH"

        (
            enabled,
            bind_address,
            port,
            autodetect_enabled,
            autodetect_address,
            sockets
        ) = default.props()

        eth_bind_addr_from_conf = cp.get(section, "bind_address",
                                         fallback=bind_address)

        eth_auto_enabled_from_conf = cp.getboolean(
            section, "autodetect_enabled", fallback=autodetect_enabled
        )
        eth_auto_addr_from_conf = cp.get(section, "autodetect_address",
                                         fallback=autodetect_address)

        if eth_bind_addr_from_conf == "":
            eth_bind_addr_from_conf = "0.0.0.0"

        if eth_auto_enabled_from_conf and eth_auto_addr_from_conf == "":
            eth_auto_addr_from_conf = resolve_broadcast_address()

        sockets_from_conf_raw = cp.get(section, "socket", fallback=None)
        if sockets_from_conf_raw is None:
            sockets_from_conf_raw = sockets
        else:
            sockets_from_conf_raw = split_lines(sockets_from_conf_raw)

        # noinspection PyTypeChecker
        sockets_from_conf: SocketsType = {}

        for socket in sockets_from_conf_raw:
            parts = socket.split(";")
            sockets_from_conf[int(parts[0])] = {
                SocketDataType.BIT: [x.strip() for x in parts[1].split(",")],
                SocketDataType.UINT: [x.strip() for x in parts[2].split(",")],
                SocketDataType.LONG: [x.strip() for x in parts[3].split(",")]
            }

        return cls.create(
            cp.getboolean(section, "enabled", fallback=enabled),
            eth_bind_addr_from_conf,
            cp.getint(section, "port", fallback=port),
            eth_auto_enabled_from_conf,
            eth_auto_addr_from_conf,
            sockets_from_conf
        )
