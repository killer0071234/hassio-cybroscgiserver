import calendar
import datetime
import os
import re
from functools import lru_cache
from math import floor
from typing import Optional, List, Type, Dict, Union, Any

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

from project.main.models import Plant

PATTERN_FILE = re.compile(r'<file>(.*?)</file>', re.DOTALL | re.IGNORECASE)
PATTERN_TEXT = re.compile(r'<text>(.*?)</text>', re.DOTALL | re.IGNORECASE)
PATTERN_VALUE = re.compile(r'<value>(.*?)</value>', re.DOTALL | re.IGNORECASE)


class CybroObject(object):
    id = 0
    params: List[Dict[str, Union[str, bool, List[str]]]] = []
    live_object = True
    rw_access = False

    def __init__(self, rw_access: bool = False):
        self.params = []
        self.define_params()
        self.rw_access = rw_access

    def __str__(self):
        return f"CybroObject: {self.get_type()}"

    def define_params(self):
        # set default params for all objects
        self.set_param_value({"name": "type", "default": self.get_type()})
        self.set_param_value({"name": "var", "default": ""})

    def set_param_value(self, param):
        param.update({"value": param["default"]})

        n = 0
        for p in self.params:
            if p["name"] == param["name"]:
                self.params[n].update(param)
                return
            n += 1
        self.params.append(param)

    def get_type(self) -> str:
        return "unknown"

    def get_toolbaricon(self):
        return os.path.join(
            finders.find(f"/img/objects/{self.get_type()}.png")
        )

    def get_params(self):
        res = []
        for p in self.params:
            res.append((p["name"], p["default"]))
        return res

    @lru_cache
    def _get_param_pattern(self, param_name: str) -> re.Pattern:
        return re.compile(r'<%s>(.*?)</%s>' % (param_name, param_name),
                          re.DOTALL | re.IGNORECASE)

    def set_params(self, id: int, s: str) -> None:
        self.id = f"c_{self.get_type()}_{id}"

        n = 0
        for param in self.params:
            p = self._get_param_pattern(param["name"])
            m = p.search(s)

            if m is not None:
                self.params[n].update({"name": param["name"],
                                       "value": m.group(1).strip()})
            n += 1

    def get_param_value(self, param: str):
        for p in self.params:
            if p["name"] == param:
                return p["value"] if len(p["value"]) else p["default"]
        return ""

    def params_to_dict(self,
                       additional_params: Optional[Dict[str, Any]] = None):
        if additional_params is None:
            additional_params = {}
        values: Dict[str, Any] = {"id": self.id}
        for p in self.params:
            name = p["name"]
            if isinstance(name, str):
                values.update({name: p["value"]})
            else:
                raise ValueError()
        values.update(additional_params)
        values.update({
            "rw_access": self.rw_access,
        })
        return values

    def create_code(self, code):
        values = self.params_to_dict({"code": code})
        return render_to_string(
            template_name=f"objects/{self.get_type()}.html",
            context=values
        )

    def create_object_html(self):
        return self.create_code("html").strip()

    def create_js_includes(self):
        return render_to_string(
            f"objects/{self.get_type()}.html",
            {"code": "js_includes"}
        )

    def create_tag_update_func(self):
        values = self.params_to_dict({"code": "tag_update_func"})
        return render_to_string(
            template_name=f"objects/{self.get_type()}.html",
            context=values
        )

    def create_tag_update_code(self):
        return self.create_code("tag_update_code").strip()

    def create_init_jq_binding(self):
        values = self.params_to_dict({"code": "init_jq_binding"})
        return render_to_string(
            template_name=f"objects/{self.get_type()}.html",
            context=values
        )

    def create_page_load_init_code(self):
        values = self.params_to_dict({"code": "page_load_init"})
        return render_to_string(
            template_name=f"objects/{self.get_type()}.html",
            context=values
        )


class CybroObjectDecimal(CybroObject):
    def get_type(self):
        return "decimal"

    def define_params(self):
        CybroObject.define_params(self)
        self.set_param_value({"name": "decimals", "default": "0"})
        self.set_param_value({"name": "digits", "default": "5"})
        self.set_param_value({
            "name": "zeroblanking",
            "default": "1",
            "select": ["0", "1"]
        })
        self.set_param_value({
            "name": "groupdigits",
            "default": "0",
            "select": ["0", "1"]
        })


class CybroObjectBargraph(CybroObject):
    def get_type(self):
        return "bargraph"

    def define_params(self):
        CybroObject.define_params(self)
        self.set_param_value({
            "name": "barstyle",
            "default": "horizontal",
            "select": ["horizontal", "vertical"]
        })
        self.set_param_value({"name": "min", "default": "0"})
        self.set_param_value({"name": "max", "default": "100"})
        self.set_param_value({"name": "size", "default": "100"})
        self.set_param_value({"name": "tickness", "default": "12"})
        self.set_param_value({"name": "color", "default": "#1F91C1"})
        self.set_param_value({"name": "bgcolor", "default": "transparent"})


class CybroObjectToggle(CybroObject):
    def get_type(self):
        return "toggle"

    def define_params(self):
        CybroObject.define_params(self)
        self.set_param_value({"name": "max", "default": "1"})
        self.set_param_value({"name": "values", "default": ""})
        self.set_param_value({"name": "value", "default": ""})
        self.set_param_value({"name": "digits", "default": "4"})
        self.set_param_value({"name": "color", "default": "#EFEFEF"})

    def set_params(self, id: int, s: str):
        CybroObject.set_params(self, id, s)

        values = PATTERN_VALUE.findall(s)
        if not values:
            values = self.get_param_value("values")
            if values:
                values = values.split(",")

        if not values:
            value_count = self.get_param_value("max")
            try:
                value_count = int(value_count) + 1
            except:
                value_count = 2
            values = list(range(0, value_count))
            change_values = [i + 0.5 for i in range(0, value_count - 1)]
        else:
            value_count = len(values)
            change_values = [
                (float(values[i]) + float(values[i + 1])) / 2
                for i in range(0, value_count - 1)
            ]

        self.set_param_value({
            "name": "values",
            "default": values
        })
        self.set_param_value({
            "name": "change_values",
            "default": change_values
        })
        self.set_param_value({
            "name": "value_count",
            "default": value_count
        })


class CybroObjectIncDec(CybroObject):
    def get_type(self):
        return "incdec"

    def define_params(self):
        CybroObject.define_params(self)
        self.set_param_value({"name": "min", "default": "0"})
        self.set_param_value({"name": "max", "default": "9999"})
        self.set_param_value({"name": "step", "default": "1"})
        self.set_param_value({"name": "decimals", "default": "0"})
        self.set_param_value({"name": "digits", "default": "4"})
        self.set_param_value({"name": "color", "default": "#EFEFEF"})


class CybroObjectSubmit(CybroObject):
    def get_type(self):
        return "submit"

    def define_params(self):
        CybroObject.define_params(self)
        self.set_param_value({"name": "min", "default": "0"})
        self.set_param_value({"name": "max", "default": "9999"})
        self.set_param_value({"name": "decimals", "default": "0"})
        self.set_param_value({"name": "digits", "default": "4"})
        self.set_param_value({"name": "color", "default": "#EFEFEF"})


class CybroObjectTimeplot(CybroObject):
    period_select = ["quarter", "hour", "day", "month", "year"]

    def get_type(self):
        return "timeplot"

    def define_params(self):
        CybroObject.define_params(self)

        bool_select = ["0", "1"]

        self.set_param_value({
            "name": "graphstyle",
            "default": "line",
            "select": ["line", "bars"]
        })
        self.set_param_value({"name": "width", "default": "750"})
        self.set_param_value({"name": "height", "default": "250"})
        self.set_param_value({"name": "min", "default": "0"})
        self.set_param_value({"name": "max", "default": "auto"})
        self.set_param_value({"name": "color", "default": ""})
        self.set_param_value({"name": "decimals", "default": "0"})
        self.set_param_value({
            "name": "download",
            "default": "1",
            "select": bool_select
        })

        self.set_param_value({
            "name": "span",
            "default": "day",
            "select": self.period_select
        })
        self.set_param_value({"name": "spancount", "default": "1"})
        self.set_param_value({
            "name": "spanmin",
            "default": "hour",
            "select": self.period_select
        })
        self.set_param_value({
            "name": "spanmax",
            "default": "day",
            "select": self.period_select
        })
        self.set_param_value({"name": "datetime", "default": ""})
        self.set_param_value({
            "name": "timeskip",
            "default": "1",
            "select": bool_select
        })
        self.set_param_value({
            "name": "cumulative",
            "default": "0",
            "select": bool_select
        })
        self.set_param_value({"name": "resolution", "default": ""})
        self.set_param_value({"name": "showlegend", "default": "true"})
        self.set_param_value({"name": "legendlabel", "default": ""})
        self.set_param_value({"name": "legendunit", "default": ""})

        self.live_object = False

    def set_params(self, id: int, s: str):
        CybroObject.set_params(self, id, s)

        values = self.get_param_value("var").split(",")
        for n, v in enumerate(values):
            v = v.strip()
            self.set_param_value({"name": f"value{n}", "default": v})

        self.set_param_value({"name": "value_count",
                              "default": str(len(values))})

        values = self.get_param_value("color").split(",")
        for n, v in enumerate(values):
            v = v.strip()
            self.set_param_value({"name": f"color{n}", "default": v})

        values = self.get_param_value("legendlabel").split(",")
        for n, v in enumerate(values):
            v = v.strip()
            self.set_param_value({"name": f"legendlabel{n}", "default": v})

    def params_to_dict(self, additional_params=None):
        if additional_params is None:
            additional_params = {}

        values = CybroObject.params_to_dict(self, additional_params)

        tags = []
        colors = []
        legendlabels = []

        try:
            tags_count = int(self.get_param_value("value_count"))
        except (AttributeError, ValueError):
            tags_count = 0

        for i in range(tags_count):
            tags.append(self.get_param_value(f"value{i}"))
            colors.append(self.get_param_value(f"color{i}"))
            legendlabels.append(self.get_param_value(f"legendlabel{i}"))

        values.update({"tags": tags})
        values.update({"colors": colors})
        values.update({"legendlabels": legendlabels})

        return values

    def create_code(self, code):
        values = self.params_to_dict({"code": code})
        now = datetime.datetime.now()

        year_range = range(2010, now.year + 1)

        try:
            spancount = int(self.get_param_value("spancount"))
        except:
            spancount = 1

        # check initial datetime
        try:
            dt = datetime.datetime.strptime(self.get_param_value("datetime"),
                                            "%Y-%m-%d %H:%M")
        except:
            dt = now

            if spancount > 1:
                span = self.get_param_value("span")
                if span == 'quarter':
                    dt -= datetime.timedelta(minutes=spancount - 15)
                elif span == "hour":
                    dt -= datetime.timedelta(hours=spancount - 1)
                elif span == "day":
                    dt -= datetime.timedelta(days=spancount - 1)
                elif span == "month":
                    month = (dt.month - spancount + 1) % 12
                    year = int(dt.year + (dt.month - spancount + 1) / 12)
                    # correct day in month if out of range
                    day = min(dt.day, calendar.monthrange(year, month)[1])
                    dt = datetime.datetime(
                        year, month, day, dt.hour, dt.hour, dt.minute
                    )
                elif span == "year":
                    # don't let year go below valid year range
                    year = min(dt.year - spancount + 1, min(year_range))
                    dt = datetime.datetime(
                        year, dt.month, dt.day, dt.hour, dt.hour, dt.minute
                    )
                now = dt

        try:
            spanmin_index = self.period_select.index(
                self.get_param_value("spanmin")
            )
        except:
            spanmin_index = 0

        try:
            spanmax_index = self.period_select.index(
                self.get_param_value("spanmax")
            )
        except:
            spanmax_index = len(self.period_select) - 1

        valid_spanrange = range(spanmin_index, spanmax_index + 1)

        values.update({
            "quarter": [0, 15, 30, 45],
            "hours": [f"{h:02d}" for h in range(0, 24)],
            "days": range(1, 32),
            "months": range(1, 13),
            "years": year_range,
            "default_quarter": floor(dt.minute / 15),
            "default_hour": dt.hour,
            "default_day": dt.day,
            "default_month": dt.month,
            "default_year": dt.year,
            "select_quarter":
                self.period_select.index("quarter") in valid_spanrange,
            "select_hours":
                self.period_select.index("hour") in valid_spanrange,
            "select_days":
                self.period_select.index("day") in valid_spanrange,
            "select_months":
                self.period_select.index("month") in valid_spanrange,
            "select_years":
                self.period_select.index("year") in valid_spanrange,
        })

        return render_to_string(f"objects/{self.get_type()}.html", values)


class CybroObjectAlarmList(CybroObject):
    def get_type(self):
        return "alarm_list"

    def define_params(self):
        CybroObject.define_params(self)
        self.set_param_value({"name": "controller", "default": ""})
        self.set_param_value({"name": "items", "default": "10"})
        self.set_param_value({
            "name": "download",
            "default": "1",
            "select": ["0", "1"]
        })


# 3PORT/VINP class bitlist 01.02.2013
class CybroObjectBitlist(CybroObject):
    def get_type(self):
        return "bitlist"

    def define_params(self):
        CybroObject.define_params(self)
        self.set_param_value({"name": "files", "default": ""})
        self.set_param_value({"name": "file", "default": ""})
        self.set_param_value({"name": "values", "default": ""})
        self.set_param_value({"name": "value", "default": ""})
        self.set_param_value({"name": "value_count", "default": "0"})
        self.set_param_value({
            "name": "action",
            "default": "0",
            "select": ["0", "1"]
        })

    def set_params(self, id: int, s: str):
        CybroObject.set_params(self, id, s)

        files = PATTERN_FILE.findall(s)
        if not files:
            files = self.get_param_value("files").split(",")

        file_str = "["
        for n, v in enumerate(files):
            if n > 0:
                file_str += ","
            file_str += f'"{str(v.strip())}"'

        file_str += "]"

        self.set_param_value({"name": "files", "default": file_str})

        values = PATTERN_VALUE.findall(s)
        if not values:
            values = self.get_param_value("values")
            if values:
                values = values.split(",")

        value_count = len(files)

        if not values:
            values = list(range(0, value_count))
            change_values = [i + 0.5 for i in range(0, value_count - 1)]
        else:
            change_values = [
                (float(values[i]) + float(values[i + 1])) / 2
                for i in range(0, value_count - 1)
            ]

        self.set_param_value({"name": "values", "default": values})
        self.set_param_value({
            "name": "change_values",
            "default": change_values
        })
        self.set_param_value({"name": "value_count", "default": value_count})


# 3PORT/VINP class textlist 04.02.2013
class CybroObjectTextlist(CybroObject):
    def get_type(self):
        return "textlist"

    def define_params(self):
        CybroObject.define_params(self)
        self.set_param_value({"name": "texts", "default": ""})
        self.set_param_value({"name": "text", "default": ""})
        self.set_param_value({"name": "values", "default": ""})
        self.set_param_value({"name": "value", "default": ""})
        self.set_param_value({
            "name": "action",
            "default": "0",
            "select": ["0", "1"]
        })

    def set_params(self, id: int, s: str):
        CybroObject.set_params(self, id, s)

        texts = PATTERN_TEXT.findall(s)
        if not texts:
            texts = self.get_param_value("texts").split(",")

        texts_str = "["
        for n, v in enumerate(texts):
            if n > 0:
                texts_str += ","
            texts_str += "\"" + str(v.strip()) + "\""

        texts_str += "]"

        self.set_param_value({"name": "texts", "default": texts_str})

        values = PATTERN_VALUE.findall(s)
        if not values:
            values = self.get_param_value("values")
            if values:
                values = values.split(",")

        value_count = len(texts)

        if not values:
            values = list(range(0, value_count))
            change_values = [i + 0.5 for i in range(0, value_count - 1)]
        else:
            change_values = [
                (float(values[i]) + float(values[i + 1])) / 2
                for i in range(0, value_count - 1)
            ]

        self.set_param_value({"name": "values", "default": values})
        self.set_param_value({
            "name": "change_values",
            "default": change_values
        })
        self.set_param_value({"name": "value_count", "default": value_count})


class ObjectFactory:
    objects: Optional[List[Type[CybroObject]]] = None
    tags: Optional[List[str]] = None
    cybro_objects: Optional[Dict[str, Type[CybroObject]]] = None
    cybro_objects_indexed: Optional[List[str]] = None
    plant: Optional[Plant] = None

    def __init__(self, plant: Plant):
        self.tags: List[str] = []
        self.cybro_objects: Dict[str, Type[CybroObject]] = {}
        self.cybro_objects_indexed: List[str] = []
        self.objects: List[CybroObject] = []

        self.plant = plant

        self.register_object(CybroObjectDecimal)
        self.register_object(CybroObjectBargraph)
        self.register_object(CybroObjectToggle)
        self.register_object(CybroObjectIncDec)
        self.register_object(CybroObjectSubmit)
        self.register_object(CybroObjectTimeplot)
        self.register_object(CybroObjectAlarmList)
        self.register_object(CybroObjectBitlist)
        self.register_object(CybroObjectTextlist)

    def register_object(self, obj_class: Type[CybroObject]):
        object_type = obj_class().get_type()
        self.cybro_objects_indexed.append(object_type)
        self.cybro_objects[object_type] = obj_class

    def create_object_by_type(self, obj_type: str) -> Optional[CybroObject]:
        try:
            return self.cybro_objects[obj_type]()
        except:
            return None

    def create_object(self, obj_type: str, params: str, rw_access: bool):
        try:
            obj = self.cybro_objects[obj_type](rw_access)
            obj.set_params(len(self.objects) + 1, params)

            # get tag for comm_req update, only for live objects
            if obj.live_object:
                tag = obj.get_param_value("var")
                if not isinstance(tag, str):
                    raise ValueError("tag is not string")
                elif len(tag) != 0:
                    try:
                        # test if tag is not in list
                        self.tags.index(tag)
                    except ValueError:
                        self.tags += [tag]

            self.objects.append(obj)
            return obj
        except:
            return None

    def create_html(self, update_period: int) -> str:
        js_includes = ""
        tag_update_func = ""
        init_jq_binding = ""
        tag_update_code = ""
        page_load_init = ""
        live = False

        # get common html sections
        for obj_type in self.cybro_objects:
            obj = self.cybro_objects[obj_type]()
            # check if object is used on this page
            for page_obj in self.objects:
                if page_obj.get_type() == obj.get_type():
                    js_includes += page_obj.create_js_includes()
                    tag_update_func += page_obj.create_tag_update_func()
                    init_jq_binding += page_obj.create_init_jq_binding()
                    break

        # get object dependent code
        for page_obj in self.objects:
            live |= page_obj.live_object
            tag_update_code += page_obj.create_tag_update_code()
            page_load_init += page_obj.create_page_load_init_code()

        if len(self.objects) != 0:
            return render_to_string(
                "objects/common_js.html",
                {
                    "update_period": update_period,
                    "live": live,
                    "plant": self.plant,
                    "tags": self.tags,
                    "request_url": "&".join(self.tags),
                    "js_includes": js_includes,
                    "tag_update_code": tag_update_code,
                    "tag_update_func": tag_update_func,
                    "init_jq_binding": init_jq_binding,
                    "page_load_init": page_load_init,
                }
            )
        else:
            return ""

    # methods called from templates
    def get_objects_html_tags(self):
        res = ["cybro", "template", "name", "search", "replace"]

        for obj_type in self.cybro_objects:
            obj = self.cybro_objects[obj_type]()
            for p in obj.params:
                name = p["name"]
                if name not in res:
                    if isinstance(name, str):
                        res.append(name)
                    else:
                        raise ValueError()

        return ",".join(res)

    def get_toolbar_object_list(self) -> str:
        res: List[str] = []
        for obj_type in self.cybro_objects_indexed:
            obj = self.cybro_objects[obj_type]()
            res.append("obj_" + obj.get_type())
        return ",".join(res)
