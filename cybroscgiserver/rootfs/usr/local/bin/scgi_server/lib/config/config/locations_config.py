from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union

from lib.general.paths import APP_DIR


@dataclass(frozen=True)
class LocationsConfig:
    @classmethod
    def create(
        cls,
        app_dir_str: Path,
        log_dir_str: Path,
        alc_dir_str: Path
    ):
        app_dir = cls._to_path(app_dir_str, APP_DIR)
        log_dir = cls._to_path(log_dir_str, app_dir)
        alc_dir = cls._to_path(alc_dir_str, app_dir)

        return cls(
            app_dir,
            log_dir,
            alc_dir
        )

    app_dir: Path
    log_dir: Path
    alc_dir: Path

    def props(self) -> Tuple[str, str, str]:
        return (
            self.app_dir.as_posix(),
            self.log_dir.as_posix(),
            self.alc_dir.as_posix()
        )

    @classmethod
    def load(cls, cp: ConfigParser, default: 'Config'):
        section = "LOCATIONS"

        (
            app_dir,
            log_dir,
            alc_dir
        ) = default.props()

        return cls.create(
            app_dir,
            cp.get(section, "log_dir", fallback=log_dir),
            cp.get(section, "alc_dir", fallback=alc_dir)
        )

    @classmethod
    def _to_path(cls, path_str: Union[str, Path], base: Path) -> Path:
        result = Path(path_str)
        return result if result.is_absolute() \
            else base.joinpath(result).resolve()
