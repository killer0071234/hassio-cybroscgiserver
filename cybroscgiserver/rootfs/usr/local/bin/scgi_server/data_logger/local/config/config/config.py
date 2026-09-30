from configparser import ConfigParser, ParsingError
from dataclasses import dataclass
from typing import Tuple

from lib.config.config.alias_config import AliasConfig
from data_logger.local.config.config.dbase_config import DbaseConfig
from lib.config.config.debuglog_config import DebugLogConfig
from lib.config.config.locations_config import LocationsConfig
from lib.config.config.scgi_config import ScgiConfig
from lib.config.errors import ConfigError
from lib.config.ini_config_parser import IniConfigParser


@dataclass(frozen=True)
class Config:
    scgi_config: ScgiConfig
    dbase_config: DbaseConfig
    locations_config: LocationsConfig
    alias_config: AliasConfig
    debuglog_config: DebugLogConfig

    def props(self) -> Tuple[
        ScgiConfig, DbaseConfig, LocationsConfig, AliasConfig,
        DebugLogConfig
    ]:
        return (
            self.scgi_config,
            self.dbase_config,
            self.locations_config,
            self.alias_config,
            self.debuglog_config
        )

    @classmethod
    def load(cls, parser: IniConfigParser, default: 'Config'):
        (
            scgi_client_config,
            dbase_config,
            locations_config,
            alias_config,
            debuglog_config
        ) = default.props()

        try:
            return cls(
                ScgiConfig.load(parser, scgi_client_config),
                DbaseConfig.load(parser, dbase_config),
                LocationsConfig.load(parser, locations_config),
                AliasConfig.load(parser, alias_config),
                DebugLogConfig.load(parser, debuglog_config)
            )
        except ParsingError as e:
            raise ConfigError("Can't read config file") from e
        except ValueError as e:
            raise ConfigError(e)
