from dataclasses import dataclass


@dataclass(frozen=True)
class CanConfig:
    @classmethod
    def create(
            cls,
            enabled: bool,
            channel: str,
            interface: str,
            bitrate: int
    ):
        return cls(
            enabled,
            channel,
            interface,
            bitrate
        )

    enabled: bool
    channel: str
    interface: str
    bitrate: int

    def props(self) -> tuple[bool, str, str, int]:
        return self.enabled, self.channel, self.interface, self.bitrate

    @classmethod
    def load(cls, cp: 'ConfigParser', default: 'Config'):
        section = "CAN"

        enabled, channel, interface, bitrate = default.props()

        return cls.create(cp.getboolean(section, "enabled", fallback=enabled),
                          cp.get(section, "channel", fallback=channel),
                          cp.get(section, "interface", fallback=interface),
                          cp.getint(section, "bitrate", fallback=bitrate))
