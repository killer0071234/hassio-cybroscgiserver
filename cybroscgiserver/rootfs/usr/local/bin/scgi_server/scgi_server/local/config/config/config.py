from configparser import ConfigParser, ParsingError
from dataclasses import dataclass

from scgi_server.local.config.config.abus_config import AbusConfig
from lib.config.config.alias_config import AliasConfig
from scgi_server.local.config.config.cache_config import CacheConfig
from scgi_server.local.config.config.can_config import CanConfig
from lib.config.config.debuglog_config import DebugLogConfig
from scgi_server.local.config.config.eth_config import EthConfig
from lib.config.config.locations_config import LocationsConfig
from scgi_server.local.config.config.push_config import PushConfig
from lib.config.config.scgi_config import ScgiConfig
from scgi_server.local.config.config.static_plcs_config import \
    StaticPlcsConfig
from lib.config.errors import ConfigError


@dataclass(frozen=True)
class Config:
    eth_config: EthConfig
    push_config: PushConfig
    can_config: CanConfig
    abus_config: AbusConfig
    cache_config: CacheConfig
    scgi_config: ScgiConfig
    locations_config: LocationsConfig
    debuglog_config: DebugLogConfig
    static_plcs_config: StaticPlcsConfig
    alias_config: AliasConfig

    def props(self) -> tuple[
        EthConfig, PushConfig, CanConfig, AbusConfig, CacheConfig, ScgiConfig,
        LocationsConfig, DebugLogConfig, StaticPlcsConfig, AliasConfig
    ]:
        return (
            self.eth_config,
            self.push_config,
            self.can_config,
            self.abus_config,
            self.cache_config,
            self.scgi_config,
            self.locations_config,
            self.debuglog_config,
            self.static_plcs_config,
            self.alias_config
        )

    @classmethod
    def load(cls, parser: ConfigParser, default: 'Config'):
        (
            eth_config,
            push_config,
            can_config,
            abus_config,
            cache_config,
            scgi_config,
            locations_config,
            debuglog_config,
            _,
            alias_config
        ) = default.props()

        try:
            return cls(
                EthConfig.load(parser, eth_config),
                PushConfig.load(parser, push_config),
                CanConfig.load(parser, can_config),
                AbusConfig.load(parser, abus_config),
                CacheConfig.load(parser, cache_config),
                ScgiConfig.load(parser, scgi_config),
                LocationsConfig.load(parser, locations_config),
                DebugLogConfig.load(parser, debuglog_config),
                StaticPlcsConfig.load(parser),
                AliasConfig.load(parser, alias_config)
            )
        except ParsingError as e:
            raise ConfigError("Can't read config file") from e
        except ConfigError as e:
            raise ConfigError(e)
