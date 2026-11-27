import http.client
import re
from dataclasses import dataclass
from functools import lru_cache, cached_property
from typing import Optional, Union, Tuple, Dict, List, Any

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse

from project.main.models import Controller, CustomUser
from project.main.page import show

UserType = Union[User, CustomUser, AnonymousUser]


def frontpage(request):
    return show(request, 1)


def split_key_value(param: str) -> Tuple[str, str]:
    try:
        key, value = param.split("=")
    except (AttributeError, ValueError):
        key, value = param, ""
    return key, value


@dataclass(frozen=True)
class ControllerData:
    controller: Optional[Controller] = None

    @staticmethod
    def from_nad(nad) -> 'ControllerData':
        try:
            c = Controller.objects.get(nad=nad, active=True)
        except Controller.DoesNotExist:
            c = None

        return ControllerData(c)

    @cached_property
    def is_valid(self) -> bool:
        return self.controller is not None

    @cached_property
    def _has_plant(self) -> bool:
        return self.is_valid and \
            self.controller.plant_id is not None and \
            self.controller.plant_id != 0

    @cached_property
    def is_plant_public(self) -> bool:
        return self._has_plant and self.controller.plant.public

    @lru_cache(maxsize=1)
    def is_user_plant_admin(self, user: UserType) -> bool:
        return self._has_plant and \
            self.controller.plant.is_user_plant_admin(user)

    @lru_cache(maxsize=1)
    def is_user_plant_user(self, user: UserType) -> bool:
        return self._has_plant and \
            self.controller.plant.is_user_plant_user(user)

    @lru_cache(maxsize=1)
    def can_write_vars(self, user: UserType) -> bool:
        return self._has_plant and \
            self.controller.plant.user_has_rw_access(user)

    @lru_cache(maxsize=1)
    def can_read_vars(self, user: UserType) -> bool:
        return self.is_plant_public or \
            self.is_user_plant_admin(user) or \
            self.is_user_plant_user(user)


def _read_params(request: WSGIRequest) -> List[Dict[str, str]]:
    args: List[Dict[str, str]] = []

    if request.method == "POST":
        for tag in request.POST.get("url").split("&"):
            key, _ = split_key_value(tag)
            args.append({"key": key, "value": ""})
    else:
        for tag in request.META.get('QUERY_STRING', '').split("&"):
            # skip time value
            if tag.find("=") != -1:
                key, value = split_key_value(tag)
                args.append({"key": key, "value": value})

    return args


def _has_admin_access(user: Any) -> bool:
    return user.is_authenticated and user.permissions.is_server_admin


def _send_scgi_request(checked_tags: List[str]) -> HttpResponse:
    query_string = "&".join(checked_tags)
    if query_string == "":
        return HttpResponse("")

    conn = http.client.HTTPConnection(host=settings.SCGI_HOST,
                                      port=settings.SCGI_PORT)
    conn.request("GET", "/?" + query_string)
    resp = conn.getresponse()
    if resp.status == 200:
        return HttpResponse(resp.read(),
                            content_type="text/xml; charset=iso-8859-1")
    else:
        return HttpResponse('')

def _get_nad(value: str) -> Optional[str]:
    try:
        nad = re.match(r"^(c\d+)\.", value).group(1)
    except AttributeError:
        nad = None
    return nad

def create_comm_request(request: WSGIRequest) -> HttpResponse:
    checked_tags: List[str] = []
    nads: Dict[str, ControllerData] = {}

    admin_access = _has_admin_access(request.user)
    args = _read_params(request)

    for arg in args:
        key = arg["key"]
        value = arg["value"]

        nad = _get_nad(key)

        if nad is not None:
            if nad in nads:
                cdata = nads[nad]
            else:
                cdata = ControllerData.from_nad(nad)
                nads.update({nad: cdata})

            if cdata.is_valid:
                if value == "":
                    if cdata.can_read_vars(request.user) or admin_access:
                        checked_tags.append(key)
                elif cdata.can_write_vars(request.user) or admin_access:
                    checked_tags.append("%s=%s" % (key, value))
        else:
            if admin_access:
                checked_tags.append("%s=%s" % (key, value))

    return _send_scgi_request(checked_tags)
