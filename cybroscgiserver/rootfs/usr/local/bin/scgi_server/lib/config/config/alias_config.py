from configparser import NoSectionError, ConfigParser


class AliasConfig:
    aliases: dict[str, str]
    _reversed: dict[str, str]

    def __init__(self, aliases: dict[str, str]):
        for val in aliases.values():
            if not val.replace("_", "").isalnum():
                raise ValueError(f"Alias name can contain only alphanumeric "
                                 f"characters: '{val}'")
        self.aliases = aliases
        self._reversed = {v: k for k, v in aliases.items()}

    @property
    def reversed(self) -> dict[str, str]:
        return self._reversed

    def props(self) -> dict[str, str]:
        return self.aliases

    @classmethod
    def load(cls, cp: ConfigParser, default: 'Config'):
        section = "ALIAS"

        aliases = default.props()

        try:
            aliases_from_conf = dict(cp.items(section))
        except NoSectionError:
            aliases_from_conf = aliases

        return cls(aliases_from_conf)
