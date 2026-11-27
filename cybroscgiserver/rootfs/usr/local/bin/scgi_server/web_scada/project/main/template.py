from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import render

from project.main.models import Template
from project.main.object_factory import ObjectFactory


@login_required
def list_templates(request: HttpRequest):
    if not request.user.permissions.can_manage_templates:
        return HttpResponseRedirect("/")

    items = Template.objects.all().order_by("order")

    return render(
        request,
        "template/list.html",
        {
            "items": items,
            "active_menu": "templates",
        }
    )


@login_required
def edit(request: HttpRequest, id: int = 0):
    if not request.user.permissions.can_manage_templates:
        return HttpResponseRedirect("/")

    tid = int(id)
    new_item = id == 0

    if not new_item:
        try:
            item = Template.objects.get(id=tid)
        except Template.DoesNotExist:
            new_item = True

    if new_item:
        item = Template()

    if request.method == "POST":
        def get_value(key):
            return request.POST.get(key, "")

        if get_value("operation") == "delete":
            item.delete()
        else:
            if new_item:
                item.author = request.user
                item.order = Template.objects.count()

            item.name = get_value("name")
            item.description = get_value("description")
            item.content = get_value("content")
            item.modified_by = request.user
            item.save()

        return HttpResponseRedirect("/template/list/")

    return render(
        request,
        "page/edit.html",
        {
            "item": item,
            "object_factory": ObjectFactory(None),
            "is_template": True,
            "active_menu": "templates",
        }
    )


@login_required
def delete(request: HttpRequest, id: int):
    if not request.user.permissions.can_manage_templates:
        return HttpResponseRedirect("/")

    try:
        item = Template.objects.get(id=id)
        item.delete()
    except Template.DoesNotExist:
        pass

    return HttpResponseRedirect("/template/list/")


@login_required
def toggle_published(request: HttpRequest, id: int):
    if not request.user.permissions.can_manage_templates:
        return HttpResponseRedirect("/")

    try:
        item = Template.objects.get(id=id)
        item.published = not item.published
        item.save()
    except Template.DoesNotExist:
        pass

    return HttpResponseRedirect("/template/list/")


@login_required
def change_order(request: HttpRequest, id: int, direction: str):
    if not request.user.permissions.can_manage_templates:
        return HttpResponseRedirect("/")

    try:
        template = Template.objects.get(id=id)
        template.normalize_order()
    except Template.DoesNotExist:
        return HttpResponseRedirect("/")

    templates = Template.objects.all()

    if direction == "up":
        for p in templates:
            if p.order == template.order - 1:
                p.order += 1
                template.order -= 1
                p.save()
                template.save()
                break
    elif direction == "dn":
        for p in templates:
            if p.order == template.order + 1:
                p.order -= 1
                template.order += 1
                p.save()
                template.save()
                break

    return HttpResponseRedirect("/template/list/")
