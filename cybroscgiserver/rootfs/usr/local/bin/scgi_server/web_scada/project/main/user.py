import json
import re

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest, \
    HttpResponseForbidden
from django.shortcuts import render

from project.main.models import CustomUser, UserPermissions, Page, \
    Controller, UserSubscriptions, Plant, Template


def _username_exists(username):
    return CustomUser.objects.filter(username=username).count() != 0


def _valid_email(email):
    result = False

    if len(email) > 7:
        pattern = r"^[_.0-9a-z-]+@([0-9a-z][0-9a-z-]+.)+[a-z]{2,4}$"
        if re.match(pattern, email) is not None:
            result = True

    return result


def check_username_password(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = auth.authenticate(username=username, password=password)

        if user and user.is_active:
            user.backend = "project.accounts.backends.CustomUserModelBackend"
            auth.login(request, user)
            return HttpResponse("1")

    return HttpResponse("0")


def username_exists(request, username):
    return HttpResponse(f"{int(_username_exists(username))}")


def valid_email(request, email = ""):
    return HttpResponse(f"{int(_valid_email(email))}")


def login(request):
    err = False

    if request.method == "POST":
        nx = request.POST.get("next", "/")
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = auth.authenticate(username=username, password=password)

        if user and user.is_active:
            # correct password and user is marked as active
            user.backend = "project.accounts.backends.CustomUserModelBackend"
            auth.login(request, user)
            return HttpResponseRedirect(nx)
        else:
            err = True
    else:
        nx = request.GET.get("next", "")

    return render(
        request,
        "user/login.html",
        {
            "next": nx,
            "err": err,
        }
    )


@login_required
def signout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')


@login_required
def list_users(request):
    if not request.user.permissions.can_manage_users:
        return HttpResponseRedirect("/")

    if request.user.permissions.is_server_admin:
        items = CustomUser.objects.all().order_by("creator__username",
                                                  "username")
    else:
        items = request.user.get_descendants()

    return render(
        request,
        "user/list.html",
        {
            "items": items,
            "active_menu": "users",
        }
    )


@login_required
def edit(request: HttpRequest, id=0, profile_edit=False):
    id = int(id)
    new_item = id == 0

    if not new_item:
        try:
            item = CustomUser.objects.get(id=id)
        except CustomUser.DoesNotExist:
            new_item = True

    if new_item:
        item = CustomUser()

    editing_self_profile = item == request.user

    if not (request.user.permissions.can_manage_users or editing_self_profile):
        return HttpResponseRedirect("/")

    if request.method == "POST":
        def get_value(key):
            return request.POST.get(key, "")

        if get_value("operation") == "delete":
            item.delete()
        else:
            if new_item:
                perm = UserPermissions()
                perm.save()
                item.permissions = perm
                subs = UserSubscriptions()
                subs.save()
                item.subscriptions = subs
                item.username = get_value("username")
                item.creator = request.user

            item.name = get_value("name")
            item.email = get_value("email")

            if "creator" in request.POST:
                item.creator_id = get_value("creator")

            pass1 = get_value("password1")
            pass2 = get_value("password2")

            if len(pass1) != 0 and pass1 == pass2:
                item.set_password(pass1)

            if not editing_self_profile:
                if request.user.permissions.is_server_admin:
                    item.permissions.is_server_admin = \
                        get_value("is_server_admin") != ""
                if request.user.permissions.can_manage_site_content:
                    item.permissions.can_manage_site_content = \
                        get_value("can_manage_site_content") != ""
                if request.user.permissions.can_manage_plants:
                    item.permissions.can_manage_plants = \
                        get_value("can_manage_plants") != ""
                if request.user.permissions.can_manage_users:
                    item.permissions.can_manage_users = \
                        get_value("can_manage_users") != ""
                if request.user.permissions.can_manage_templates:
                    item.permissions.can_manage_templates = \
                        get_value("can_manage_templates") != ""
                if request.user.permissions.can_manage_controllers:
                    item.permissions.can_manage_controllers = \
                        get_value("can_manage_controllers") != ""
                if request.user.permissions.can_manage_media:
                    item.permissions.can_manage_media = \
                        get_value("can_manage_media") != ""
                if request.user.permissions.rw_tags_access:
                    item.permissions.rw_tags_access = \
                        get_value("rw_tags_access") != ""
                item.is_staff = item.permissions.is_server_admin
                item.is_superuser = item.is_staff
                item.permissions.save()
                
            item.subscriptions.alarms_events_subscription = \
                get_value("alarms_events_subscription") != ""
            item.subscriptions.save()

            item.last_ip = request.META.get("REMOTE_ADDR")
            item.save()

            if (
                not editing_self_profile or
                request.user.permissions.can_manage_users
            ):
                homepages = request.POST.get("homepages").split(",")

                # delete deselected homepages
                for p in item.homepages.all():
                    if not str(p.id) in homepages:
                        item.homepages.remove(p)
                        # remove user from plant
                        plant = p.get_plant()
                        if plant is not None:
                            plant.users.remove(item)

                # add selected pages
                for hid in homepages:
                    if hid != '':
                        try:
                            p = Page.objects.get(id=hid)
                            if p not in item.homepages.all():
                                item.homepages.add(p)

                            plant = p.get_plant()
                            if (
                                plant is not None and
                                item not in plant.users.all()
                            ):
                                plant.users.add(item)
                        except Page.DoesNotExist:
                            pass

        return HttpResponseRedirect("/" if profile_edit else "/user/list/")

    plant_pages = request.user.get_all_plants_pages()

    if not new_item:
        homepages = item.homepages.all()
        for p in plant_pages:
            p.is_homepage = p in homepages
    else:
        homepages = None

    return render(
        request,
        "user/edit.html",
        {
            "item": item,
            "plant_pages": plant_pages,
            "user_management": not profile_edit,
            "active_menu": "users",
            "homepages": homepages,
            "controllers":
                Controller
                .objects
                .filter(owner=item)
                .order_by("date_added") if not new_item else [],
        }
    )


@login_required
def edit_profile(request):
    return edit(request, request.user.id, True)


@login_required
def delete(request, id):
    if not request.user.permissions.can_manage_users:
        return HttpResponseRedirect("/")

    try:
        user = CustomUser.objects.get(id=id)
        users = [user] + user.get_descendants()

        for user in users:
            user.delete()
    except Exception as ex:
        raise ex

    return HttpResponseRedirect("/user/list/")


@login_required
def toggle_active(request, id):
    if not request.user.permissions.can_manage_users:
        return HttpResponseRedirect("/")

    try:
        user = CustomUser.objects.get(id=id)
        user.is_active = not user.is_active
        user.save()
    except CustomUser.DoesNotExist:
        pass

    return HttpResponseRedirect("/user/list/")


@login_required
def related(request):
    if not request.user.permissions.can_manage_users:
        return HttpResponseForbidden()

    rels = {}
    for user in CustomUser.objects.all():
        rel = {}
        for controller in Controller.objects.filter(Q(owner=user) |
                                                    Q(created=user)):
            key = f'Controller({controller.id})'
            if controller.owner == user:
                rel.setdefault(key, []).append('owner')
            if controller.created == user:
                rel.setdefault(key, []).append('created')

        for cuser in CustomUser.objects.filter(creator=user):
            rel.setdefault(f'User({cuser.id})', []).append('creator')

        for page in Page.objects.filter(Q(author=user) | Q(modified_by=user)):
            key = f'Page({page.id})'
            if page.author == user:
                rel.setdefault(key, []).append('author')
            if page.modified_by == user:
                rel.setdefault(key, []).append('modified_by')

        for plant in Plant.objects.filter(Q(author=user) |
                                          Q(modified_by=user) |
                                          Q(admins=user) |
                                          Q(users=user)):
            key = f'Plant({plant.id})'
            if plant.author == user:
                rel.setdefault(key, []).append('author')
            if plant.modified_by == user:
                rel.setdefault(key, []).append('modified_by')
            if plant.admins.filter(id=user.id).count() > 0:
                rel.setdefault(key, []).append('admins')
            if plant.users.filter(id=user.id).count() > 0:
                rel.setdefault(key, []).append('users')

        for tpl in Template.objects.filter(Q(author=user) |
                                           Q(modified_by=user)):
            key = f'Template({tpl.id})'
            if tpl.author == user:
                rel.setdefault(key, []).append('author')
            if tpl.modified_by == user:
                rel.setdefault(key, []).append('modified_by')

        rels[user.id] = rel
    return HttpResponse(json.dumps(rels, indent=2),
                        content_type="application/json")


@login_required
def get_available_user_list(request):
    items = CustomUser.objects.filter(is_active = True)

    return render(
        request,
        "user/available_user_list.html",
        {
            "items": items,
        }
    )


@login_required
def get_user_list_row(request, id):
    try:
        return render(
            request,
            "user/user_list_row.html",
            {
                "user": CustomUser.objects.get(id=id),
            }
        )
    except CustomUser.DoesNotExist:
        return HttpResponse("")
