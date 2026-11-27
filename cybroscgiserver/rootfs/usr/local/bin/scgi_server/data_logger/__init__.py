import sys
from asyncio import AbstractEventLoop

from data_logger.local.config.config.config import Config
from data_logger.local.config.config.config_defaults import DEFAULT_CONFIG
from data_logger.local.container import Container
from lib.config.loader import read_config_from_file
from lib.general.paths import CONFIG_FILE
from lib.startup.init_logging import init_logging
from lib.startup.runner import run_simple


async def main(main_loop: AbstractEventLoop) -> None:
    config = read_config_from_file(CONFIG_FILE, Config, DEFAULT_CONFIG)
    init_logging(config.debuglog_config,
                 config.locations_config.log_dir,
                 "data_logger")

    container = Container(config, main_loop, sys.argv[0])

    await container.data_logger_bootstrap.run()


if __name__ == '__main__':
    run_simple(main)
