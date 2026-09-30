import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render

import settings.settings
from project.main.models import Plant, Page, CustomUser, Controller


@login_required
def list_plants(request):
    if not request.user.can_manage_plants():
        return HttpResponseRedirect("/")

    if request.user.permissions.can_manage_plants:
        items = Plant.objects.all().order_by("order")
    else:
        items = (
            Plant
            .objects
            .filter(admins__in=[request.user])
            .order_by("order")
        )

    return render(
        request,
        "plant/list.html",
        {
            "items" : items,
            "active_menu": "plants",
        }
    )


@login_required
def edit(request, id=0):
    id = int(id)
    new_item = id == 0

    if not new_item:
        try:
            item = Plant.objects.get(id = id)
        except Plant.DoesNotExist:
            new_item = True

    if new_item:
        if not request.user.permissions.can_manage_plants:
            return HttpResponseRedirect("/")
        item = Plant()
        item.author = request.user
    else:
        if not request.user.can_manage_plant(item):
            return HttpResponseRedirect("/")

    if request.method == "POST":
        operation = request.POST.get("operation", "")

        if operation == "delete":
            item.delete()
        else:
            backlink = "/plant/list/"

            item.name = request.POST.get("name", "").strip()
            item.description = request.POST.get("description", "")
            item.content = request.POST.get("content", "")
            item.timezone = request.POST.get("timezone", "UTC") 
            item.modified_by = request.user

            if len(item.name) == 0:
                return HttpResponseRedirect(backlink)

            if new_item:
                page = Page()
                page.name = item.name
                page.parent = None
                page.public = item.public
                page.update_period_id = 3
                page.published = True
                page.author = request.user
                page.modified_by = request.user
                page.order = 0

                data_root = settings.settings.DATA_FOLDER_ROOT
                dedicated_data_folder = page.get_dedicated_data_folder()
                if not os.path.exists(data_root + dedicated_data_folder):
                    os.makedirs(data_root + dedicated_data_folder)
                page.data_folder = dedicated_data_folder

                page.save()

                item.author = request.user
                item.order = Plant.objects.count()
                item.homepage = page

            item.save()

            admins = request.POST.get("admins", "").split(",")
            if admins[0] == "":
                admins = []

            # delete deselected admins
            for p in item.admins.all():
                if not "%d" % p.id in admins:
                    item.admins.remove(p)

            # add selected admins
            for aid in admins:
                try:
                    user = CustomUser.objects.get(id=aid)
                    if not user in item.admins.all():
                        item.admins.add(user)
                except CustomUser.DoesNotExist:
                    pass

            controllers = request.POST.get("controllers", "").split(",")

            # delete deselected controllers
            for c in Controller.objects.filter(plant=item):
                if str(c.id) not in controllers:
                    c.plant = None
                    c.save()

            # add selected controllers
            for cid in controllers:
                if cid == '':
                    continue

                try:
                    c = Controller.objects.get(id=cid)
                    c.plant = item
                    c.save()
                except Controller.DoesNotExist:
                    pass

            item.save()

            if new_item:
                page.plant = item
                page.save()

        return HttpResponseRedirect(backlink)

    return render(
        request,
        "plant/edit.html",
        {
            "item": item,
            "controllers":
                Controller
                .objects
                .filter(plant=item)
                .order_by("nad") if not new_item else [],
            "active_menu": "plants",
        }
    )


@login_required
def change_order(request, id, direction):
    if not request.user.can_manage_plants():
        return HttpResponseRedirect("/")

    try:
        plant = Plant.objects.get(id = id)
    except Plant.DoesNotExist:
        return HttpResponseRedirect("/")

    plants = Plant.objects.all()

    if direction == "up":
        for p in plants:
            if p.order == plant.order - 1:
                p.order += 1
                plant.order -= 1
                p.save()
                plant.save()
                break

    elif direction == "dn":
        for p in plants:
            if p.order == plant.order + 1:
                p.order -= 1
                plant.order += 1
                p.save()
                plant.save()
                break

    Plant.normalize_order()

    return HttpResponseRedirect("/plant/list/")


@login_required
def delete(request, id):
    if not request.user.can_manage_plants():
        return HttpResponseRedirect("/")

    try:
        item = Plant.objects.get(id=id)
        item.delete()

        for n, plant in enumerate(Plant.objects.all().order_by("order")):
            plant.order = n
            plant.save()
    except Plant.DoesNotExist:
        pass

    return HttpResponseRedirect("/plant/list/")


@login_required
def toggle_public(request, id):
    try:
        item = Plant.objects.get(id=id)

        if not request.user.can_manage_plant(item):
            return HttpResponseRedirect("/")

        item.public = not item.public
        item.save()

        item.homepage.public = item.public
        item.homepage.save()
    except Plant.DoesNotExist:
        pass

    return HttpResponseRedirect("/plant/list/")
