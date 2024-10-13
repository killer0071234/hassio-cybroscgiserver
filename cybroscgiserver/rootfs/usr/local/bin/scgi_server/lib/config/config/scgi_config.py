from configparser import ConfigParser
from dataclasses import dataclass


@dataclass(frozen=True)
class ScgiConfig:
    scgi_bind_address: str
    scgi_port: int
    request_timeout_s: int
    reply_with_descriptions: bool
    tls_enabled: bool
    access_token: str | None
    server_address: str | None
    keepalive: float

    def props(self) -> tuple[
        str, int, int, int, bool, bool, str | None, str | None, float
    ]:
        return (
            self.scgi_bind_address,
            self.scgi_port,
            self.request_timeout_s,
            self.reply_with_descriptions,
            self.tls_enabled,
            self.access_token,
            self.server_address,
            self.keepalive
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
            keepalive
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
            cp.getfloat(section, "keepalive", fallback=keepalive)
        )