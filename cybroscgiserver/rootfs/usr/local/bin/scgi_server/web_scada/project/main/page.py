import re
from typing import Optional, Union

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.shortcuts import render

from project.main.models import Page, UpdatePeriod, Plant, Template, \
    Controller, CustomUser
from project.main.object_factory import ObjectFactory

PATTERN_CONTROLLER = re.compile(r'<var>(.*)\..*</var>',
                                re.DOTALL | re.IGNORECASE)
PATTERN_CYBRO = re.compile(r'<cybro>(.*?)</cybro>', re.DOTALL | re.IGNORECASE)
PATTERN_NAME = re.compile(r'<name>(.*?)</name>', re.DOTALL | re.IGNORECASE)
PATTERN_SEARCH_REPLACE = re.compile(
    r'<search>(.*?)</search>.*?<replace>(.*?)</replace>',
    re.DOTALL | re.IGNORECASE
)
PATTERN_TYPE = re.compile(r'<type>(.*?)</type>', re.DOTALL | re.IGNORECASE)
PATTERN_TEMPLATE = re.compile(r'<template>(.*?)</template>',
                              re.DOTALL | re.IGNORECASE)


def render_page(page: Page, user: Union[CustomUser, AnonymousUser]) -> str:
    # if cache is enabled
    if settings.PAGE_CACHE_VALIDITY != 0:
        cache_key = page.get_cache_key()
        content = cache.get(cache_key)

        if content is not None:
            return content

    update_period = 10000

    if page.update_period is not None:
        update_period = page.update_period.get_period_ms()

    def parse_template_tag(match) -> str:
        params = match.group(1)

        m = PATTERN_NAME.search(params)
        if m is not None:
            replaces = []

            try:
                template = Template.objects.get(name=m.group(1),
                                                published=True)
                matches = PATTERN_SEARCH_REPLACE.findall(params)

                if matches:
                    for m in matches:
                        replaces.append((m[0], m[1]))
            except:
                return ""

            tpl_content = template.content
            for r in replaces:
                tpl_content = tpl_content.replace(r[0], r[1])

            return tpl_content
        else:
            return ""

    def parse_cybro_tag(groups) -> str:
        nonlocal factory
        nonlocal plant
        nonlocal user

        params = groups.group(1)
        if params is None:
            return ""

        rw_access = user.is_authenticated and user.permissions.is_server_admin
        if not rw_access:
            c = PATTERN_CONTROLLER.search(params)
            if c is not None:
                nad = c.group(1)
                try:
                    controller = Controller.objects.get(nad=nad, active=True)
                except Controller.DoesNotExist:
                    controller = None

                if controller is not None and \
                    plant is not None and \
                    controller.plant_id == plant.id:
                    rw_access = plant.user_has_rw_access(user)

        m = PATTERN_TYPE.search(params)
        if m is not None:
            object_type = m.group(1)
            obj = factory.create_object(object_type, params, rw_access)
            if obj is not None:
                return obj.create_object_html()

        return ""

    plant = page.get_plant()
    factory = ObjectFactory(plant)

    template_html = PATTERN_TEMPLATE.sub(parse_template_tag, page.content)
    html = PATTERN_CYBRO.sub(parse_cybro_tag, template_html)

    content = html + factory.create_html(update_period)

    if settings.PAGE_CACHE_VALIDITY != 0:
        cache.set(cache_key, content, settings.PAGE_CACHE_VALIDITY)

    return content


def show(request: HttpRequest, id: Optional[Union[str, int]]):
    try:
        pgid = int(id) if id is not None else 1
    except (TypeError, ValueError):
        pgid = 1

    try:
        page = Page.objects.get(id=pgid)
    except Page.DoesNotExist:
        if pgid == 1:
            raise Exception()
        else:
            return HttpResponseRedirect("/")

    if not page.can_user_access(request.user):
        return HttpResponseRedirect("/")

    children = []
    if len(page.content) != 0:
        page_content = render_page(page, request.user)
    else:
        page_content = ""
        for p in page.get_children():
            if p.can_user_access(request.user):
                children.append(p)

    if page.can_user_edit(request.user):
        plant = page.get_plant()
        plant_id = plant.id if plant is not None else 0
        page_edit_link = f"/page/edit/{plant_id}/{page.id}/"
    else:
        page_edit_link = ""

    if pgid == 1:
        if (
            request.user.is_authenticated and
            request.user.permissions.can_manage_plants
        ):
            plants = Plant.objects.all().order_by("order")
        else:
            query = Q(public=True)
            if request.user.is_authenticated:
                query |= Q(admins__in=[request.user]) | \
                         Q(users__in=[request.user])
            plants = Plant.objects.filter(query).distinct().order_by("order")
    else:
        plants = None

    return render(
        request,
        "page/show.html",
        {
            "page": page,
            "page_content": page_content,
            "current_page": page,
            "page_edit_link": page_edit_link,
            "children": children,
            "plants": plants,
        }
    )


@login_required
def list_pages(request):
    return HttpResponse("")


@login_required
def plant_page_list(request: HttpRequest, id: int):
    try:
        plant = Plant.objects.get(id=id)

        if not request.user.can_manage_plant(plant):
            return HttpResponseRedirect("/")
    except Plant.DoesNotExist:
        return HttpResponseRedirect("/")

    items = [plant.homepage] + plant.homepage.get_descendants()

    return render(
        request,
        "page/list.html",
        {
            "editing_site_content": False,
            "items": items,
            "plant": plant,
            "plant_id": plant.id,
            "active_menu": "plants",
        }
    )


@login_required
def site_list(request: HttpRequest):
    if not request.user.permissions.can_manage_site_content:
        return HttpResponseRedirect("/")

    return render(
        request,
        "page/list.html",
        {
            "editing_site_content": True,
            "items": request.user.get_all_site_pages(),
            "plant_id": 0,
            "active_menu": "site_content",
        }
    )


@login_required
def edit(request: HttpRequest,
         plant_id: Union[str, int],
         id: Union[str, int] = 0):
    plant_id = int(plant_id)
    pgid = int(id)
    plant = None
    new_item = pgid == 0
    site_page = plant_id == 0

    if not new_item:
        try:
            item = Page.objects.get(id=pgid)
        except Page.DoesNotExist:
            new_item = True

    try:
        plant = Plant.objects.get(id=plant_id)

        if not plant.can_user_manage_content(request.user):
            return HttpResponseRedirect("/")
    except Plant.DoesNotExist:
        # site content
        if not request.user.permissions.can_manage_site_content:
            return HttpResponseRedirect("/")

    if new_item:
        item = Page()
        item.plant = plant
        if plant is not None:
            item.parent = item.plant.homepage

    editing_root_page = not (new_item or item.parent is not None)

    if request.method == "POST":
        operation = request.POST.get("operation", "")

        if operation == "delete":
            item.delete()
        else:
            try:
                period = UpdatePeriod.objects.get(
                    id=request.POST.get("update_period", "0")
                )
            except UpdatePeriod.DoesNotExist:
                period = None

            item.name = request.POST.get("name", "")
            item.description = request.POST.get("description", "")
            item.content = request.POST.get("content", "")
            item.update_period = period
            item.modified_by = request.user

            if not editing_root_page:
                item.parent_id = request.POST.get("parent", None)

            if new_item:
                item.author = request.user
                item.order = Page.objects.count()

            item.save()
            item.delete_cache()

            if request.POST.get("order_changed", "") == "1":
                n = 0
                while True:
                    pgid = int(request.POST.get("order_%d" % n, "-1"))

                    if pgid == 0:
                        pgid = item.id

                    if pgid != -1:
                        Page.objects.filter(id=pgid).update(order=n)
                    else:
                        break
                    n += 1

        backlink = "/page/site_list/" \
            if site_page \
            else f"/plant/page_list/{plant_id}/"

        if operation == "preview":
            return HttpResponseRedirect(item.get_link())
        elif operation == "back_to_manage":
            return HttpResponseRedirect(backlink)
        else:
            pass

    if new_item:
        item.author = request.user
        if site_page:
            item.update_period_id = 7  # never
        else:
            try:
                item.update_period = UpdatePeriod.objects.get(period=60)
            except UpdatePeriod.DoesNotExist:
                pass

    # delete current path for media browser
    if "current_path" in request.session:
        del request.session["current_path"]

    return render(
        request,
        "page/edit.html",
        {
            "item": item,
            "is_site_page": site_page,
            "object_factory": ObjectFactory(item.get_plant()),
            "enable_order_edit": item.get_siblings_with_self().count() > 1,
            "update_periods": UpdatePeriod.objects.all().order_by("period"),
            "editing_root_page": editing_root_page,
            "plant_id": plant_id,
            "active_menu": "site_content" if site_page else "plants"
        }
    )


@login_required
def get_order_area(request: HttpRequest, parent_page: str, current_page: str):
    parent_page = int(parent_page)
    current_page = int(current_page)
    current_item = None
    new_item = current_page == 0

    if not new_item:
        try:
            current_item = Page.objects.get(id=current_page)
        except Page.DoesNotExist:
            new_item = True

    if new_item:
        current_item = Page(id=0, name="[ new page ]")

    items = Page.objects.filter(parent__id=parent_page).order_by("order")

    if len(items) != 0:
        return render(
            request,
            "page/edit_order.html",
            {
                "items": items,
                "current_item": current_item,
                "add_item": (
                    current_item.id == 0 or
                    current_item.parent.id != parent_page
                ),
            }
        )
    else:
        return HttpResponse("")


@login_required
def delete(request: HttpRequest,
           plant_id: Union[str, int] = 0,
           id: Union[str, int] = 0):
    plid = int(plant_id)
    pgid = int(id)

    try:
        plant = Plant.objects.get(id=plid)

        if not plant.can_user_manage_content(request.user):
            return HttpResponseRedirect("/")
    except Plant.DoesNotExist:
        # site content
        if not request.user.permissions.can_manage_site_content:
            return HttpResponseRedirect("/")

    try:
        item = Page.objects.get(id=pgid)

        for p in item.get_descendants():
            p.delete()

        item.delete()
    except Page.DoesNotExist:
        pass

    return HttpResponseRedirect(
        "/page/site_list/"
        if plid == 0
        else f"/plant/page_list/{plid}/"
    )


@login_required
def toggle_public(request: HttpRequest,
                  plant_id: Union[str, int] = 0,
                  id: Union[str, int] = 0):
    plid = int(plant_id)
    pgid = int(id)

    try:
        plant = Plant.objects.get(id=plid)

        if not plant.can_user_manage_content(request.user):
            return HttpResponseRedirect("/")
    except Plant.DoesNotExist:
        # site content
        if not request.user.permissions.can_manage_site_content:
            return HttpResponseRedirect("/")

    try:
        item = Page.objects.get(id=pgid)
        item.public = not item.public
        item.save()
    except Page.DoesNotExist:
        pass

    return HttpResponseRedirect(
        "/page/site_list/"
        if plid == 0
        else f"/plant/page_list/{plid}/"
    )


@login_required
def toggle_published(request: HttpRequest,
                     plant_id: Union[str, int] = 0,
                     id: Union[str, int] = 0):
    plid = int(plant_id)
    pgid = int(id)

    try:
        plant = Plant.objects.get(id=plid)

        if not plant.can_user_manage_content(request.user):
            return HttpResponseRedirect("/")
    except Plant.DoesNotExist:
        # site content
        if not request.user.permissions.can_manage_site_content:
            return HttpResponseRedirect("/")

    try:
        item = Page.objects.get(id=pgid)
        item.published = not item.published
        item.save()
    except Page.DoesNotExist:
        pass

    return HttpResponseRedirect(
        "/page/site_list/"
        if plid == 0
        else f"/plant/page_list/{plid}/"
    )


def redirect_highslide_statics(request: HttpRequest, image: str):
    return HttpResponseRedirect(f"{settings.STATIC_URL}/inc/js/{image}")
