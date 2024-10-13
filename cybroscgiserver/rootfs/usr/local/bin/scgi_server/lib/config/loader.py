from collections import OrderedDict
from configparser import ConfigParser

from lib.config.errors import ConfigError


class ConfigLoaderError(Exception):
    pass


class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super().__setitem__(key, value)


def create_config_parser() -> ConfigParser:
    return ConfigParser(dict_type=MultiOrderedDict, strict=False)


def read_config_from_file(config_file: str,
                          config_class,
                          defaults):
    """Reads config from init file into Config object.
    """
    # Normal dict is replaced with custom to allow multiple occurrence of the
    # same key in one section.
    cp = create_config_parser()

    try:
        if len(cp.read(config_file)) == 0:
            print(f"Configuration file '{config_file}' not found, using "
                  f"default values")
    except ConfigError as e:
        raise ConfigLoaderError("Can't read config file") from e

    return config_class.load(cp, defaults)
