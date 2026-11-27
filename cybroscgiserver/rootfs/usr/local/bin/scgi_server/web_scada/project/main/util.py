import datetime

import pytz
from django.utils import timezone


def nad_str_to_nad(value):
    import re
    try:
        return int(re.match(r"^c(\d+)", value).group(1))
    except (AttributeError, ValueError):
        return 0


def localize_timestamp(timestamp: datetime.datetime) -> datetime.datetime:
    return timestamp.astimezone(timezone.get_current_timezone()) \
        if timestamp is not None else None


def localize_timestamp_with_zone(tz, ts):
    now = datetime.datetime.now(pytz.utc)
    try:
        if tz:
            tz = pytz.timezone(tz)
            if tz:
                now = now.astimezone(tz)
                td = now.utcoffset()
                return ts + td
    except:
        pass
    return ts


def localize_timestamp_with_tzinfo(ts, tzinfo):
    now = datetime.datetime.now(pytz.utc)
    if tzinfo:
        now = now.astimezone(tzinfo)
        td = now.utcoffset()
        return ts + td
    return ts


def str_to_float(s: str, default: float = 0.0) -> float:
    try:
        return float(s.replace(",", "."))
    except (AttributeError, ValueError):
        return default


def str_to_int(s: str, default: int = 0) -> int:
    try:
        return int(s)
    except (AttributeError, ValueError):
        return default
