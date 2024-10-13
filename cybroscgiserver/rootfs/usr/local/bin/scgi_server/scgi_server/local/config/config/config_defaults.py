from datetime import timedelta
from pathlib import Path

from scgi_server import Config
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
from lib.general.paths import APP_DIR

DEFAULT_CONFIG = Config(
    EthConfig(
        enabled=True,
        bind_address="0.0.0.0",
        port=8442,
        autodetect_enabled=True,
        autodetect_address="",
        sockets={}
    ),
    PushConfig(
        enabled=False,
        timeout_h=timedelta(hours=24)
    ),
    CanConfig(
        enabled=False,
        channel="can0",
        interface="socketcan_native",
        bitrate=100000
    ),
    AbusConfig(
        timeout_ms=timedelta(milliseconds=200),
        number_of_retries=3,
        password=None
    ),
    CacheConfig(
        request_period=timedelta(seconds=0),
        valid_period=timedelta(seconds=0),
        cleanup_period_s=timedelta(seconds=0)
    ),
    ScgiConfig(
        scgi_bind_address='',
        scgi_port=4000,
        request_timeout_s=10,
        reply_with_descriptions=True,
        tls_enabled=False,
        access_token=None,
        server_address=None,
        keepalive=.0
    ),
    LocationsConfig(
        app_dir=APP_DIR,
        log_dir=Path("./log"),
        alc_dir=Path("./alc")
    ),
    DebugLogConfig(
        enabled=True,
        log_to_file=True,
        verbose_level="DEBUG",
        max_log_file_size_kb=1024,
        max_log_backup_count=5
    ),
    StaticPlcsConfig(
        static_plcs_configs=[]
    ),
    AliasConfig(
        aliases={}
    )
)