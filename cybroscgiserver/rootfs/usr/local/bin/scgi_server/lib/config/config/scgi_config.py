from configparser import ConfigParser
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ScgiConfig:
    scgi_bind_address: str
    scgi_port: int
    request_timeout_s: int
    reply_with_descriptions: bool
    tls_enabled: bool
    access_token: Optional[str]
    server_address: Optional[str]
    keepalive: float
    only_user_variables: bool

    def props(self) -> Tuple[
        str, int, int, bool, bool, Optional[str], Optional[str], float, bool
    ]:
        return (
            self.scgi_bind_address,
            self.scgi_port,
            self.request_timeout_s,
            self.reply_with_descriptions,
            self.tls_enabled,
            self.access_token,
            self.server_address,
            self.keepalive,
            self.only_user_variables
        )

    @classmethod
    def load(cls, cp: ConfigParser, default: 'Config'):
        section = "SCGI"

        (
            scgi_bind_address,
            scgi_port,
            request_timeout_s,
            reply_with_descriptions,
            tls_enabled,
            access_token,
            server_address,
            keepalive,
            only_user_variables
        ) = default.props()

        scgi_bind_addr_from_conf = cp.get(section, "bind_address",
                                          fallback=scgi_bind_address)
        scgi_access_token_from_conf = cp.get(section, "token",
                                             fallback=access_token)
        if scgi_access_token_from_conf == "":
            scgi_access_token_from_conf = None

        return cls(
            scgi_bind_addr_from_conf,
            cp.getint(section, "port", fallback=scgi_port),
            cp.getint(section, "timeout_s", fallback=request_timeout_s),
            cp.getboolean(section, "reply_with_descriptions",
                          fallback=reply_with_descriptions),
            cp.getboolean(section, "tls_enabled", fallback=tls_enabled),
            scgi_access_token_from_conf,
            cp.get(section, "server_address", fallback=server_address),
            cp.getfloat(section, "keepalive", fallback=keepalive),
            cp.getboolean(section, "only_user_variables",
                          fallback=only_user_variables),
        )