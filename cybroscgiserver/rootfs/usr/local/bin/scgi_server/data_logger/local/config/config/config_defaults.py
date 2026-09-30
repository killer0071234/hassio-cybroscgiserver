from pathlib import Path

from lib.config.config.alias_config import AliasConfig
from data_logger.local.config.config.dbase_config import DbaseConfig
from lib.config.config.debuglog_config import DebugLogConfig
from lib.config.config.locations_config import LocationsConfig
from lib.config.config.scgi_config import ScgiConfig
from lib.general.paths import APP_DIR
from data_logger.local.config.config.config import Config

DEFAULT_CONFIG = Config(
    ScgiConfig(
        scgi_bind_address='',
        scgi_port=4000,
        reply_with_descriptions=True,
        tls_enabled=False,
        access_token=None,
        server_address=None,
        keepalive=5.0,
        only_user_variables=False
    ),
    DbaseConfig(
        host="localhost",
        port=3306,
        name="cybro",
        user="root",
        password="root",
        max_query_size=1000000
    ),
    LocationsConfig(
        app_dir=APP_DIR,
        log_dir=Path("./log"),
        alc_dir=Path("./alc")
    ),
    AliasConfig({}),
    DebugLogConfig(
        enabled=True,
        log_to_file=True,
        verbose_level="DEBUG",
        max_log_file_size_kb=1024,
        max_log_backup_count=5
    )
)