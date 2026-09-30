from typing import Union

from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from project.main.models import Controller


@login_required
def list_controllers(request):
    if not request.user.permissions.can_manage_controllers:
        return HttpResponseRedirect("/")

    items = Controller.objects.all().order_by("nad")

    return render(
        request,
        "controller/list.html",
        {
            "items": items,
            "active_menu": "controllers",
        }
    )


@login_required
def edit(request: WSGIRequest, id: Union[str, int] = 0):
    if not request.user.permissions.can_manage_controllers:
        return HttpResponseRedirect("/")

    ctrl_id = int(id)
    if ctrl_id != 0:
        try:
            item = Controller.objects.get(id=ctrl_id)
        except Controller.DoesNotExist:
            item = Controller()
            item.created = request.user
    else:
        item = None

    if request.method == "POST":
        def get_value(key):
            return request.POST.get(key, "")

        if get_value("operation") == "delete":
            item.delete()
        else:
            item.nad = get_value("nad")
            item.location = get_value("location")
            item.function = get_value("function")
            item.save()

        return HttpResponseRedirect("/controller/list/")

    return render(
        request,
        "controller/edit.html",
        {
            "item": item,
            "active_menu": "controllers",
        }
    )


@login_required
def delete(request, id):
    if not request.user.permissions.can_manage_controllers:
        return HttpResponseRedirect("/")

    try:
        Controller.objects.get(id=id).delete()
    except Controller.DoesNotExist:
        pass

    return HttpResponseRedirect("/controller/list/")


@login_required
def toggle_active(request, id):
    if not request.user.permissions.can_manage_controllers:
        return HttpResponseRedirect("/")

    try:
        item = Controller.objects.get(id=id)
        item.active = not item.active
        item.save()
    except Controller.DoesNotExist:
        pass

    return HttpResponseRedirect("/controller/list/")


@login_required
def get_available_controller_list(request):
    if request.user.permissions.is_server_admin:
        items = Controller.objects.filter(plant=None)
    else:
        items = Controller.objects.filter(owner=request.user, plant=None)

    return render(
        request,
        "controller/available_controller_list.html",
        {
            "items": items.order_by("nad"),
        }
    )


@login_required
def get_controller_list_row(request, id):
    try:
        return render(
            request,
            "controller/controller_list_row.html",
            {
                "c": Controller.objects.get(id=id),
            }
        )
    except Controller.DoesNotExist:
        return HttpResponse("")


def nad_valid(request, nad):
    try:
        valid = Controller.objects.filter(nad=nad).count() == 0
    except Controller.DoesNotExist:
        valid = False

    return HttpResponse("1" if valid else "0")
