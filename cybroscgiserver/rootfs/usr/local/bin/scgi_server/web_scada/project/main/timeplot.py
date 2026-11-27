import datetime
import math
from typing import Tuple

import pytz
from django.core.handlers.wsgi import WSGIRequest
from django.db import connection
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from project.main.models import Measurement
from project.main.models import Page
from project.main.util import localize_timestamp_with_tzinfo
from settings.settings import CSV_EXPORT_CHARSET
from settings.settings_local import TIMEPLOT_INTERPOLATION

TIMEPLOT_INTERPOLATION = \
    4 if TIMEPLOT_INTERPOLATION is None else TIMEPLOT_INTERPOLATION


class RawPoint:
    dt = 0
    r = None

    def __str__(self):
        return f"(RawPoint) dt: {self.dt}, r: {self.r}"


class CumulativePoint:
    raw_value = None
    timestamp = 0
    sample_timestamp = 0
    value = None
    x_value = 0

    def __str__(self):
        raw_value = f"{self.raw_value}" if self.raw_value is not None else "-"
        value = f"{self.value}" if self.value is not None else "-"

        return (f"{self.timestamp} ({self.sample_timestamp}) raw: {raw_value} "
                f"value: {value} (x_value: {self.x_value})")


class CumulativePoints(object):
    items = None

    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def to_timeplot(self):
        res = []
        for item in self.items:
            if item.value is not None:
                res.append(f"[{item.x_value},{item.value}]")
        return res


def get_nearest_value(tag, dt, tollerance):
    sql = """
        SELECT
            *,
            ABS(TIMEDIFF('%(dt)s', timestamp)) AS diff
        FROM `measurements`
        WHERE `tag`='%(tag)s'
        AND `timestamp` >= '%(dt_start)s'
        AND `timestamp` <= '%(dt_end)s'
        ORDER BY diff
        LIMIT 1"""

    dt_start = dt - datetime.timedelta(seconds=tollerance / 2)
    dt_end = dt + datetime.timedelta(seconds=tollerance / 2)
    sql = sql % {"dt": dt, "dt_start": dt_start, "dt_end": dt_end, "tag": tag}

    cursor = connection.cursor()
    cursor.execute(sql)
    col_names = [desc[0] for desc in cursor.description]

    row = cursor.fetchone()
    if row is None:
        return None
    else:
        row_dict = dict(zip(col_names, row))
        m = Measurement()
        m.id = row_dict["id"]
        m.nad = row_dict["nad"]
        m.tag = row_dict["tag"]
        m.value = row_dict["value"]
        m.timestamp = row_dict["timestamp"]
        return m


def get_cumulative_values(tag: str,
                          start_timestamp: datetime.datetime,
                          end_timestamp: datetime.date,
                          resolution: int,
                          spancount: int,
                          calc_x_value,
                          shift: float = 0.0):
    last_value = None
    dT = end_timestamp - start_timestamp
    full_period = dT.days * 60 * 60 * 24 + dT.seconds
    # this is the bar width
    sample_period = full_period / (resolution * spancount)
    # calculate the sampling width(nearest point range), if the bar width is
    # less than 6000sec the sampling width is equal to bar width - 1sec else
    # the sampling width is 1/10 of the bar width
    # for bar width 10min the sampling width is +-4min 59.5sec;
    # 1h : +-29min 59.5sec; 1day : +- 1/20 day; 1month : +- 1/20 month
    sample_period_width = \
        sample_period - 1 if sample_period < 6000 else sample_period / 10
    interpolation_period = \
        datetime.timedelta(seconds=sample_period * TIMEPLOT_INTERPOLATION)
    values = []
    first_value_index = None
    last_value_index = None

    dt = start_timestamp + datetime.timedelta(seconds=sample_period)
    sample_width = (
        calc_x_value((dt - start_timestamp), dt)
        if calc_x_value is not None
        else 0
    )

    max_range = resolution * spancount + 1

    # fetch all values from db
    for n in range(0, max_range):
        dt = start_timestamp + datetime.timedelta(seconds=sample_period * n)
        r = get_nearest_value(tag, dt, sample_period_width)

        p = CumulativePoint()
        p.sample_timestamp = dt
        if r is not None:
            p.timestamp = r.timestamp
            p.raw_value = float(r.value)

        values.append(p)

    # loop through sampled values and interpolate for non-existing points
    first_non_null_index = None
    last_non_null_index = 0
    for i in range(0, len(values)):
        if values[i].raw_value is not None:
            if first_non_null_index is None:
                first_non_null_index = i
            if last_non_null_index < i:
                last_non_null_index = i

    if first_non_null_index is not None:
        current_index = first_non_null_index
        current_non_null_index = current_index
        while current_index < last_non_null_index:
            if values[current_index].raw_value is not None:
                current_non_null_index = current_index
                current_index = current_index + 1
            else:
                while values[current_index].raw_value is None:
                    current_index = current_index + 1
                value_span = current_index - current_non_null_index
                if value_span <= TIMEPLOT_INTERPOLATION:
                    left_value = values[current_non_null_index].raw_value
                    right_value = values[current_index].raw_value
                    dx_value = right_value - left_value
                    for i in range (current_non_null_index + 1, current_index):
                        fact = float(i - current_non_null_index) / value_span
                        values[i].raw_value = (dx_value * fact) + left_value
        if first_non_null_index > 0:
            left_m = (
                Measurement
                .objects
                .filter(tag=tag)
                .filter(timestamp__gte=start_timestamp - interpolation_period)
                .filter(timestamp__lte=start_timestamp)
                .order_by("-timestamp")
            )[0:1]

            if len(left_m) > 0:
                ts_diff = values[first_non_null_index].sample_timestamp - \
                          left_m[0].timestamp
                ts_diff = ts_diff.days * 60 * 60 * 24 + ts_diff.seconds
                if ts_diff < sample_period * TIMEPLOT_INTERPOLATION:
                    left_value = float(left_m[0].value)
                    right_value = float(values[first_non_null_index].raw_value)
                    dx_value = right_value - left_value
                    for i in range (0, first_non_null_index):
                        ts2_diff = values[i].sample_timestamp - \
                                   left_m[0].timestamp
                        ts2_diff = float(
                            ts2_diff.days * 60 * 60 * 24 + ts2_diff.seconds
                        )
                        fact = ts2_diff / ts_diff
                        values[i].raw_value = (dx_value * fact) + left_value

        if last_non_null_index < len(values) - 1:
            right_m = (
                Measurement
                .objects
                .filter(tag=tag)
                .filter(timestamp__gte=end_timestamp)
                .filter(timestamp__lte=end_timestamp + interpolation_period)
                .order_by("timestamp")
            )[0:1]

            if len(right_m) > 0:
                ts_diff = right_m[0].timestamp - \
                          values[last_non_null_index].sample_timestamp
                ts_diff = ts_diff.days * 60 * 60 * 24 + ts_diff.seconds
                if ts_diff < sample_period * TIMEPLOT_INTERPOLATION:
                    left_value = float(values[last_non_null_index].raw_value)
                    right_value = float(right_m[0].value)
                    dx_value = right_value - left_value
                    for i in range (last_non_null_index + 1, len(values)):
                        ts2_diff = right_m[0].timestamp - \
                                   values[i].sample_timestamp
                        ts2_diff = float(
                            ts2_diff.days * 60 * 60 * 24 + ts2_diff.seconds
                        )
                        fact = ts2_diff / ts_diff
                        values[i].raw_value = (dx_value * fact) + left_value

    # loop through sampled values and calculate value and x_value for valid
    # points
    for n, p in enumerate(values):
        if p.raw_value is not None:
            dts = (p.sample_timestamp - start_timestamp)
            # umjesto dt stavi r.timestamp ako zelis x za tocno vrijeme
            # ocitanja sada je dt sto znaci da je po x-u zeljeno vrijeme
            # ocitanja
            if last_value is not None:
                p.value = p.raw_value - last_value
                if calc_x_value is not None:
                    p.x_value = calc_x_value(dts, p.sample_timestamp) - \
                                shift * sample_width

            if first_value_index is None:
                first_value_index = n

            last_value = p.raw_value
            last_value_index = n
        else:
            last_value = None

    # check for leftmost point if it is commissioning period value
    if (
        first_value_index is not None and
        first_value_index > 0 and
        len(values) != 0 and
        values[0].raw_value is None
    ):
        p = values[first_value_index]
        # get first measured value
        first_value = \
            Measurement.objects.filter(tag = tag).order_by("timestamp")[0:1]

        if len(first_value) != 0:
            first_value = first_value[0]
            # check if it is in range for display
            if start_timestamp <= first_value.timestamp <= end_timestamp:
                dts = (p.sample_timestamp - start_timestamp)
                p.value = p.raw_value - float(first_value.value)
                if calc_x_value is not None:
                    p.x_value = calc_x_value(dts, p.sample_timestamp) - \
                                shift * sample_width

    # check for rightmost point if it is current value
    if (
        last_value_index is not None and
        last_value_index < len(values) and
        len(values) != 0 and
        values[len(values) - 1].raw_value is None
    ):
        p = values[last_value_index + 1]
        # get last measured value
        last_value = \
            Measurement.objects.filter(tag=tag).order_by("-timestamp")[0:1]
        if len(last_value) != 0:
            last_value = last_value[0]
            # check if it is in range for display
            if start_timestamp <= last_value.timestamp <= end_timestamp:
                dts = p.sample_timestamp - start_timestamp
                last_shown_value = values[last_value_index].raw_value
                p.raw_value = float(last_value.value)
                if p.raw_value != last_shown_value:
                    p.timestamp = last_value.timestamp
                    p.value = p.raw_value - last_shown_value
                    if calc_x_value is not None:
                        p.x_value = calc_x_value(dts, p.sample_timestamp) - \
                                    shift * sample_width

    # if no values found, probably unfinished commissioning period
    if first_value_index is None and last_value_index is None:
        first_value = \
            Measurement.objects.filter(tag = tag).order_by("timestamp")[0:1]
        last_value = \
            Measurement.objects.filter(tag = tag).order_by("-timestamp")[0:1]

        if len(first_value) != 0 and len(last_value) != 0:
            first_value = first_value[0]
            last_value = last_value[0]
            # check if it is in range for display
            if (
                start_timestamp <= first_value.timestamp <= end_timestamp and
                start_timestamp <= last_value.timestamp <= end_timestamp
            ):
                # find sample period for last point
                for val in values:
                    if val.sample_timestamp > last_value.timestamp:
                        dts = (val.sample_timestamp - start_timestamp)
                        p = CumulativePoint()
                        p.sample_timestamp = val.sample_timestamp
                        p.timestamp = last_value.timestamp
                        p.value = float(last_value.value) - \
                                  float(first_value.value)
                        if calc_x_value is not None:
                            p.x_value = \
                                calc_x_value(dts, p.sample_timestamp) - \
                                shift * sample_width
                        values = [p]
                        break

    res = CumulativePoints()
    for p in values:
        if p.value is not None:
            res.add(p)

    return res


def get_cumulative_values_year(tag, start_timestamp, end_timestamp, tz,
                               resolution, spancount, calc_x_value, shift=0):
    last_value = None
    dT = end_timestamp - start_timestamp
    full_period = dT.days * 60 * 60 * 24 + dT.seconds
    # this is the bar width
    sample_period = full_period / (resolution * spancount)
    # calculate the sampling width(nearest point range), if the bar width is
    # less than 6000sec the sampling width is equal to bar width - 1sec else
    # the sampling width is 1/10 of the bar width
    # for bar width 10min the sampling width is +-4min 59.5sec;
    # 1h : +-29min 59.5sec; 1day : +- 1/20 day; 1month : +- 1/20 month
    sample_period_width = \
        sample_period - 1 if sample_period < 6000 else sample_period / 10
    interpolation_period = \
        datetime.timedelta(seconds = sample_period * TIMEPLOT_INTERPOLATION)
    values = []
    first_value_index = None
    last_value_index = None

    dt = start_timestamp + datetime.timedelta(seconds = sample_period)
    sample_width = (
        calc_x_value(dt - start_timestamp, dt)
        if calc_x_value is not None
        else 0
    )

    max_range = resolution * spancount + 1

    start_timestamp_zoned = datetime.datetime(start_timestamp.year,
                                              start_timestamp.month,
                                              start_timestamp.day,
                                              start_timestamp.hour,
                                              start_timestamp.minute,
                                              start_timestamp.second,
                                              tzinfo=pytz.utc)
    start_timestamp_zoned = start_timestamp_zoned.astimezone(tz)

    # fetch all values from db
    for n in range(0, max_range):
        if resolution == 12:
            # why oh why do we use a so stupid calendar!!!!!
            dt = datetime.datetime(
                int(start_timestamp_zoned.year + (n / 12)),
                1 + (n % 12),
                1,
                0,
                0,
                0,
                tzinfo=tz
            )
            dt = dt.astimezone(pytz.utc)
            dt = dt.replace(tzinfo=None)
        else:
            dt = start_timestamp + datetime.timedelta(
                seconds=sample_period * n
            )
        r = get_nearest_value(tag, dt, sample_period_width)

        p = CumulativePoint()
        p.sample_timestamp = dt
        if r is not None:
            p.timestamp = r.timestamp
            p.raw_value = float(r.value)

        values.append(p)

    # loop through sampled values and interpolate for non-existing points
    first_non_null_index = None
    last_non_null_index = 0

    for i in range(0, len(values)):
        if values[i].raw_value is not None:
            if first_non_null_index is None:
                first_non_null_index = i
            if last_non_null_index < i:
                last_non_null_index = i

    if first_non_null_index is not None:
        current_index = first_non_null_index
        current_non_null_index = current_index

        while current_index < last_non_null_index:
            if values[current_index].raw_value is not None:
                current_non_null_index = current_index
                current_index = current_index + 1
            else:
                while values[current_index].raw_value is None:
                    current_index = current_index + 1

                value_span = current_index - current_non_null_index
                if value_span <= TIMEPLOT_INTERPOLATION:
                    left_value = values[current_non_null_index].raw_value
                    right_value = values[current_index].raw_value
                    dx_value = right_value - left_value
                    for i in range (current_non_null_index + 1, current_index):
                        fact = float(i - current_non_null_index) / value_span
                        values[i].raw_value = (dx_value * fact) + left_value

        if first_non_null_index > 0:
            left_m = (
                Measurement
                .objects
                .filter(tag=tag)
                .filter(timestamp__gte=start_timestamp - interpolation_period)
                .filter(timestamp__lte=start_timestamp)
                .order_by("-timestamp")
            )[0:1]

            if len(left_m) > 0:
                ts_diff = values[first_non_null_index].sample_timestamp - \
                          left_m[0].timestamp
                ts_diff = ts_diff.days * 60 * 60 * 24 + ts_diff.seconds

                if ts_diff < sample_period * TIMEPLOT_INTERPOLATION:
                    left_value = float(left_m[0].value)
                    right_value = float(values[first_non_null_index].raw_value)
                    dx_value = right_value - left_value
                    for i in range (0, first_non_null_index):
                        ts2_diff = values[i].sample_timestamp - \
                                   left_m[0].timestamp
                        ts2_diff = float(
                            ts2_diff.days * 60 * 60 * 24 + ts2_diff.seconds
                        )
                        fact = ts2_diff / ts_diff
                        values[i].raw_value = (dx_value * fact) + left_value

        if last_non_null_index < len(values) - 1:
            right_m = (
                Measurement
                .objects
                .filter(tag=tag)
                .filter(timestamp__gte=end_timestamp)
                .filter(timestamp__lte=end_timestamp + interpolation_period)
                .order_by("timestamp")
            )[0:1]

            if len(right_m) > 0:
                ts_diff = right_m[0].timestamp - \
                          values[last_non_null_index].sample_timestamp
                ts_diff = ts_diff.days * 60 * 60 * 24 + ts_diff.seconds
                if (ts_diff < sample_period * TIMEPLOT_INTERPOLATION):
                    left_value = float(values[last_non_null_index].raw_value)
                    right_value = float(right_m[0].value)
                    dx_value = right_value - left_value
                    for i in range (last_non_null_index + 1, len(values)):
                        ts2_diff = right_m[0].timestamp - \
                                   values[i].sample_timestamp
                        ts2_diff = float(
                            ts2_diff.days * 60 * 60 * 24 + ts2_diff.seconds
                        )
                        fact = ts2_diff / ts_diff
                        values[i].raw_value = (dx_value * fact) + left_value

    # loop through sampled values and calculate value and x_value for valid
    # points
    for n, p in enumerate(values):
        if p.raw_value is not None:
            dts = (p.sample_timestamp - start_timestamp)
            # umjesto dt stavi r.timestamp ako zelis x za tocno vrijeme
            # ocitanja sada je dt sto znaci da je po x-u zeljeno vrijeme
            # ocitanja
            if last_value is not None:
                p.value = p.raw_value - last_value
                if calc_x_value is not None:
                    p.x_value = calc_x_value(dts, p.sample_timestamp) - \
                                shift * sample_width

            if first_value_index is None:
                first_value_index = n

            last_value = p.raw_value
            last_value_index = n
        else:
            last_value = None

    # check for leftmost point if it is commissioning period value
    if (
           first_value_index is not None and
           first_value_index > 0 and
           len(values) != 0 and
            values[0].raw_value is None
    ):
        p = values[first_value_index]
        # get first measured value
        first_value = \
            Measurement.objects.filter(tag = tag).order_by("timestamp")[0:1]
        if len(first_value) != 0:
            first_value = first_value[0]
            # check if it is in range for display
            if start_timestamp <= first_value.timestamp <= end_timestamp:
                dts = (p.sample_timestamp - start_timestamp)
                p.value = p.raw_value - float(first_value.value)
                if calc_x_value is not None:
                    p.x_value = calc_x_value(dts, p.sample_timestamp) - \
                                shift * sample_width

    # check for rightmost point if it is current value
    if (
           last_value_index is not None and
           last_value_index < len(values) and
           len(values) != 0 and
            values[len(values) - 1].raw_value is None
    ):
        p = values[last_value_index + 1]
        # get last measured value
        last_value = \
            Measurement.objects.filter(tag = tag).order_by("-timestamp")[0:1]
        if len(last_value) != 0:
            last_value = last_value[0]
            # check if it is in range for display
            if start_timestamp <= last_value.timestamp <= end_timestamp:
                dts = (p.sample_timestamp - start_timestamp)
                last_shown_value = values[last_value_index].raw_value
                p.raw_value = float(last_value.value)
                if p.raw_value != last_shown_value:
                    p.timestamp = last_value.timestamp
                    p.value = p.raw_value - last_shown_value
                    if calc_x_value is not None:
                        p.x_value = calc_x_value(dts, p.sample_timestamp) - \
                                    shift * sample_width

    # if no values found, probably unfinished commissioning period
    if first_value_index is None and last_value_index is None:
        first_value = \
            Measurement.objects.filter(tag = tag).order_by("timestamp")[0:1]
        last_value = \
            Measurement.objects.filter(tag = tag).order_by("-timestamp")[0:1]
        if len(first_value) != 0 and len(last_value) != 0:
            first_value = first_value[0]
            last_value = last_value[0]
            # check if it is in range for display
            if (
                start_timestamp <= first_value.timestamp <= end_timestamp and
                start_timestamp <= last_value.timestamp <= end_timestamp
            ):
                # find sample period for last point
                for val in values:
                    if val.sample_timestamp > last_value.timestamp:
                        dts = (val.sample_timestamp - start_timestamp)
                        p = CumulativePoint()
                        p.sample_timestamp = val.sample_timestamp
                        p.timestamp = last_value.timestamp
                        p.value = float(last_value.value) - \
                                  float(first_value.value)
                        if calc_x_value is not None:
                            p.x_value = \
                                calc_x_value(dts, p.sample_timestamp) - \
                                shift * sample_width
                        values = [p]
                        break

    res = CumulativePoints()
    for p in values:
        if p.value is not None:
            res.add(p)

    return res


def get_nad_variable_from_tag(tag: str) -> Tuple[str, str]:
    name, variable = tag.split(".", maxsplit=1)
    return name, variable


def get_timeplot_data(request: WSGIRequest, params: str):
    res = []

    for graph_params in params.split(";"):
        p = {}
        for param in graph_params.split(","):
            try:
                (key, value) = param.split("=")
                p[key] = value
            except:
                pass

        period = p["p"]
        tag = p["t"]
        start = p["s"]
        cumulative = p["cum"] == "1"

        try:
            spancount = int(p["sc"])
        except:
            spancount = 1
        try:
            resolution = int(p["res"])
        except:
            resolution = 10

        (
            start_year,
            start_month,
            start_day,
            start_hour,
            start_quarter
        ) = start.split(":")

        try:
            start_quarter = int(start_quarter)
        except (AttributeError, ValueError):
            start_quarter = 0
        try:
            start_hour = int(start_hour)
        except (AttributeError, ValueError):
            start_hour = 0
        try:
            start_day = int(start_day)
        except (AttributeError, ValueError):
            start_day = 1
        try:
            start_month = int(start_month)
        except (AttributeError, ValueError):
            start_month = 1
        try:
            start_year = int(start_year)
        except (AttributeError, ValueError):
            start_year = 2010

        nad, variable = get_nad_variable_from_tag(tag)
        query = Q(nad=nad, tag=variable)

        data = ""

        # added plant id for localization
        try:
            page_id = p["page"]
            plant_timezone = Page.objects.get(id=page_id).plant.timezone
            plant_timezone = pytz.timezone(plant_timezone)
        except Page.DoesNotExist:
            plant_timezone = pytz.utc

        plant_now = datetime.datetime.now(plant_timezone)

        if period == "quarter":
            start_timestamp = datetime.datetime(
                start_year, start_month, start_day,
                start_hour, start_quarter, 0,
                tzinfo=plant_timezone
            )
            start_timestamp = start_timestamp.astimezone(pytz.utc)

            span_min = spancount * 15
            end_timestamp = start_timestamp + datetime.timedelta(
                hours=int(span_min / 60),
                minutes=span_min % 60
            )

            def calc_x_value(d_ts: datetime.timedelta, *args) -> float:
                return (d_ts.seconds + d_ts.days * 86400) / 60

            if cumulative:
                data = get_cumulative_values(
                    variable, start_timestamp, end_timestamp, resolution,
                    spancount, calc_x_value, 1.0
                ).to_timeplot()
            else:
                data = []
                query &= Q(timestamp__range=(start_timestamp, end_timestamp))

                for r in (
                    Measurement.objects.filter(query).order_by("timestamp")
                ):
                    dts = (r.timestamp - start_timestamp)
                    x_value = calc_x_value(dts)
                    data.append(f"[{x_value},{r.value}]")

            data = "[" + ", ".join(data) + "]"
        elif period == "hour":
            # add plant timezone information to selected date
            start_timestamp = datetime.datetime(
                start_year, start_month, start_day,
                start_hour, 0, 0,
                tzinfo=plant_now.tzinfo
            )
            # transform to utc
            start_timestamp = start_timestamp.astimezone(pytz.utc)
            end_timestamp = start_timestamp + datetime.timedelta(
                hours=spancount
            )

            def calc_x_value(d_ts: datetime.timedelta, dt: datetime.datetime):
                return (d_ts.seconds + d_ts.days * 60 * 60 * 24) / 60

            if cumulative:
                data = get_cumulative_values(
                    variable, start_timestamp, end_timestamp, resolution,
                    spancount, calc_x_value, 1.0
                ).to_timeplot()
            else:
                data = []
                query &= Q(timestamp__range=(start_timestamp, end_timestamp))

                for r in (
                    Measurement
                    .objects
                    .filter(query)
                    .order_by("timestamp")
                ):
                    dts = (r.timestamp - start_timestamp)
                    x_value = calc_x_value(dts, r.timestamp)
                    data.append(f"[{x_value},{r.value}]")

            data = "[" + ",".join(data) + "]"
        elif period == "day":
            # add plant timezone information to selected date
            start_timestamp = datetime.datetime(
                start_year, start_month, start_day,
                0, 0, 0,
                tzinfo=plant_now.tzinfo
            )
            # transform to utc
            start_timestamp = start_timestamp.astimezone(pytz.utc)
            end_timestamp = \
                start_timestamp + datetime.timedelta(days=spancount)

            def calc_x_value(d_ts, dt):
                return d_ts.days * 24 + d_ts.seconds / 3600 + dt.minute / 60.0

            if cumulative:
                data = get_cumulative_values(
                    variable, start_timestamp, end_timestamp, resolution,
                    spancount, calc_x_value, 1.0
                ).to_timeplot()
            else:
                data = []
                query &= Q(timestamp__range=(start_timestamp, end_timestamp))

                for r in (
                    Measurement
                    .objects
                    .filter(query)
                    .order_by("timestamp")
                ):
                    dts = (r.timestamp - start_timestamp)
                    x_value = calc_x_value(dts, r.timestamp)
                    data.append(f"[{x_value},{r.value}]")

            data = "[" + ",".join(data) + "]"
        elif period == "month":
            # add plant timezone information to selected date and transform
            # to utc
            start_timestamp = datetime.datetime(
                start_year, start_month, 1,
                0, 0, 0,
                tzinfo=plant_now.tzinfo
            )
            end_month = start_month + spancount - 1
            # add plant timezone information to selected date and transform
            # to utc
            start_timestamp = start_timestamp.astimezone(pytz.utc)
            end_timestamp = datetime.datetime(
                int(start_year + end_month / 12), end_month % 12 + 1, 1,
                0, 0, 0,
                tzinfo=plant_now.tzinfo
            )
            end_timestamp = end_timestamp.astimezone(pytz.utc)

            def calc_x_value(d_ts, dt):
                return d_ts.days + 1 + (d_ts.seconds // 3600) / 24.0

            if cumulative:
                data = get_cumulative_values(
                    variable, start_timestamp, end_timestamp, resolution,
                    spancount, calc_x_value, 0.5
                ).to_timeplot()
            else:
                query &= Q(timestamp__range=(start_timestamp, end_timestamp))
                data = []
                last_x_value = None

                for r in (
                    Measurement
                    .objects
                    .filter(query)
                    .order_by("timestamp")
                ):
                    dts = (r.timestamp - start_timestamp)
                    x_value = calc_x_value(dts, r.timestamp)
                    # resolution of result is one hour
                    if last_x_value is None or last_x_value != x_value:
                        data.append(f"[{x_value},{r.value}]")
                        last_x_value = x_value

            data = "[" + ",".join(data) + "]"
        elif period == "year":
            # add plant timezone information to selected date and transform
            # to utc
            start_timestamp = datetime.datetime(
                start_year, 1, 1,
                0, 0, 0,
                tzinfo=plant_now.tzinfo
            )
            # add plant timezone information to selected date and transform
            # to utc
            end_timestamp = datetime.datetime(
                start_year + spancount, 1, 1,
                0, 0, 0,
                tzinfo=plant_now.tzinfo
            )

            start_timestamp = start_timestamp.astimezone(pytz.utc)
            end_timestamp = end_timestamp.astimezone(pytz.utc)

            # remove tzinfo
            start_timestamp = start_timestamp.replace(tzinfo=None)
            end_timestamp = end_timestamp.replace(tzinfo=None)

            def calc_x_value(d_ts, dt):
                return d_ts.days / 10.0

            if cumulative:
                data = get_cumulative_values_year(
                    variable, start_timestamp, end_timestamp, plant_now.tzinfo,
                    resolution, spancount, calc_x_value, 1
                ).to_timeplot()
            else:
                query &= Q(timestamp__range=(start_timestamp, end_timestamp))
                data = []
                last_x_value = None

                for r in (
                    Measurement
                    .objects
                    .filter(query)
                    .order_by("timestamp")
                ):
                    dts = (r.timestamp - start_timestamp)
                    x_value = calc_x_value(dts, None)

                    # filter result
                    if last_x_value is None or last_x_value != x_value:
                        data.append(f"[{x_value},{r.value}]")
                        last_x_value = x_value

            data = "[" + ",".join(data) + "]"
        else:
            pass

        res.append(data)

    return HttpResponse("\n".join(res))


def get_download_data(tags, start_timestamp, end_timestamp, tzinfo):
    data = ["date;time;" + ";".join(tags)]

    if len(tags) == 1:
        query = Q(tag=tags[0])
    else:
        query = Q(tag__in=tags)

    query &= Q(timestamp__range=(start_timestamp, end_timestamp))

    if len(tags) == 1:
        for r in Measurement.objects.filter(query).order_by("timestamp"):
            data.append("%s;%s;%s" % (
                localize_timestamp_with_tzinfo(r.timestamp, tzinfo).date(),
                localize_timestamp_with_tzinfo(r.timestamp, tzinfo).time(),
                r.value
            ))
    else:
        prev_timestamp = ""
        s = ""
        values = [""] * len(tags)

        for r in Measurement.objects.filter(query).order_by("timestamp"):
            if prev_timestamp != r.timestamp.ctime():
                if len(s) != "":
                    data.append(s + ";".join(values))
                    values = [""] * len(tags)

                prev_timestamp = r.timestamp.ctime()
                s = "%s;%s;" % (
                    localize_timestamp_with_tzinfo(r.timestamp, tzinfo).date(),
                    localize_timestamp_with_tzinfo(r.timestamp, tzinfo).time()
                )
            values[tags.index(r.tag)] = r.value

        if len(s) != "":
            data.append(s + ";".join(values))

    return "\n".join(data)


def get_cumulative_download_data(tags, start_timestamp, end_timestamp,
                                 resolution, spancount, decimals, tzinfo):
    points_table = []

    for n, tag in enumerate(tags):
        points = get_cumulative_values(
            tag, start_timestamp, end_timestamp, resolution, spancount,
            None, 0.0
        )
        points_table.append(points)

    timestamps = []

    if len(points_table) != 0:
        for p in points_table[0].items:
            timestamps.append(p.sample_timestamp)

    data = ["date;time;" + ";".join(tags)]

    for n, timestamp in enumerate(timestamps):
        row = [f"{localize_timestamp_with_tzinfo(timestamp, tzinfo).date()}",
               f"{localize_timestamp_with_tzinfo(timestamp, tzinfo).time()}"]

        for p in points_table:
            value = (
                p.items[n].value / math.pow(10, decimals)
                if p.items[n].value is not None
                else "-"
            )
            row.append(f"{value}")
        data.append(";".join(row))

    return "\n".join(data)


def get_cumulative_download_data_year(tags, start_timestamp, end_timestamp,
                                      resolution, spancount, decimals, tzinfo):
    points_table = []

    for n, tag in enumerate(tags):
        points = get_cumulative_values_year(
            tag, start_timestamp, end_timestamp, tzinfo, resolution,
            spancount, None, 0
        )
        points_table.append(points)

    timestamps = []

    if len(points_table) != 0:
        for p in points_table[0].items:
            timestamps.append(p.sample_timestamp)

    data = ["date;time;" + ";".join(tags)]

    def _localize_timestamp(ts, tzinfo):
        now = datetime.datetime.now(pytz.utc)
        if tzinfo:
            now = now.astimezone(tzinfo)
            td = now.utcoffset()
            return ts + td
        return ts

    for n, timestamp in enumerate(timestamps):
        row = [str(_localize_timestamp(timestamp, tzinfo).date()),
               str(_localize_timestamp(timestamp, tzinfo).time())]
        # added timezone localization
        for p in points_table:
            value = (
                p.items[n].value / math.pow(10, decimals)
                if p.items[n].value is not None
                else "-"
            )
            row.append(f"{value}")

        data.append(";".join(row))

    return "\n".join(data)


def download_timeplot_data(request, params):
    p = {}

    for param in params.split(","):
        try:
            (key, value) = param.split("=")
            p[key] = value
        except:
            pass

    tags = p["t"].split("+")
    period = p["p"]
    start = p["s"]
    spancount = int(p["sc"])
    cumulative = p["cum"] == "1"
    resolution = int(p["res"])
    decimals = int(p["dec"])

    # added plant timezone
    try:
        page_id = p["page"]
        plant_timezone = Page.objects.get(id=page_id).plant.timezone
        plant_timezone = pytz.timezone(plant_timezone)
    except Page.DoesNotExist:
        plant_timezone = pytz.utc

    plant_now = datetime.datetime.now(plant_timezone)
    fname = ""

    for tag in tags:
        if len(fname) == 0:
            fname = f"timeplot_{tag}_{plant_now.date()}.csv"

    (start_year, start_month, start_day, start_hour) = start.split(":")

    start_hour = int(start_hour)
    start_day = int(start_day)
    start_month = int(start_month)
    start_year = int(start_year)

    # create local time date and transform to utc
    if period == "hour":
        start_timestamp = datetime.datetime(
            start_year, start_month, start_day,
            start_hour, 0, 0,
            tzinfo=plant_now.tzinfo
        ).astimezone(pytz.utc)
        end_timestamp = start_timestamp + datetime.timedelta(hours=spancount)
    elif period == "day":
        start_timestamp = datetime.datetime(
            start_year, start_month, start_day,
            0, 0, 0,
            tzinfo=plant_now.tzinfo
        ).astimezone(pytz.utc)
        end_timestamp = start_timestamp + datetime.timedelta(days=spancount)
    elif period == "month":
        start_timestamp = datetime.datetime(
            start_year, start_month, 1,
            0, 0, 0,
            tzinfo=plant_now.tzinfo
        ).astimezone(pytz.utc)
        end_month = start_month + spancount - 1
        end_timestamp = datetime.datetime(
            int(start_year + (end_month) / 12), end_month % 12 + 1, 1,
            0, 0, 0,
            tzinfo=plant_now.tzinfo
        ).astimezone(pytz.utc)
    elif period == "year":
        start_timestamp = datetime.datetime(
            start_year, 1, 1,
            0, 0, 0,
            tzinfo=plant_now.tzinfo
        ).astimezone(pytz.utc)
        end_timestamp = datetime.datetime(
            start_year + spancount, 1,
            1, 0, 0, 0,
            tzinfo=plant_now.tzinfo
        ).astimezone(pytz.utc)
    else:
        return HttpResponse("")

    # remove tzinfo
    start_timestamp = start_timestamp.replace(tzinfo=None)
    end_timestamp = end_timestamp.replace(tzinfo=None)

    if cumulative:
        if period == "year":
            data = get_cumulative_download_data_year(
                tags, start_timestamp, end_timestamp, resolution, spancount,
                decimals, plant_now.tzinfo
            )
        else:
            data = get_cumulative_download_data(
                tags, start_timestamp, end_timestamp, resolution, spancount,
                decimals, plant_now.tzinfo
            )
    else:
        data = get_download_data(
            tags, start_timestamp, end_timestamp, plant_now.tzinfo
        )

    if CSV_EXPORT_CHARSET is not None:
        data = data.encode(CSV_EXPORT_CHARSET)

    filename = fname if len(fname) != 0 else "timeplot.csv"

    response = HttpResponse(data, content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def show_fullscreen(request, timeplot_id, graphstyle, tags, min, max, colors,
                    decimals, legend_labels, legend_unit, show_legend, page):
    tags = tags.split(",")
    colors = colors.split(",") if colors != "-" else ""
    legend_labels = legend_labels.split(",") if legend_labels != "-" else ""
    id = "timeplot_xx"
    legend_unit = legend_unit if legend_unit != "-" else ""

    content = ""

    content += render_to_string(
        template_name="objects/timeplot.html",
        context={
            "code": "js_includes",
            "fullscreen": True,
        },
        request=request
    )

    content += render_to_string(
        template_name="objects/timeplot.html",
        context={
            "code": "html",
            "fullscreen": True,
            "id": id,
            "type": "timeplot",
            "height": "500",
            "graphstyle": graphstyle,
            "value_count": len(tags),
            "tags": tags,
            "min": min,
            "max": max,
            "colors": colors,
            "decimals": decimals,
            "legendlabels": legend_labels,
            "legendunit": legend_unit,
            "showlegend": show_legend
        },
        request=request
    )

    return render(
        request,
        "objects/timeplot_fullscreen.html",
        {
            "content": content,
            "fullscreen": True,
            "tag_update_func": render_to_string(
                template_name="objects/timeplot.html",
                context={
                    "code": "tag_update_func",
                    "fullscreen": True,
                    "timeplot_id": timeplot_id,
                },
                request=request
            ),
            "page_load_init": render_to_string(
                template_name="objects/timeplot.html",
                context={
                    "code": "page_load_init",
                    "id": id,
                    "fullscreen": True,
                },
                request=request
            ),
        }
    )
