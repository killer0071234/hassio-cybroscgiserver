from django import template
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.template.defaultfilters import stringfilter
from django.template.loader import render_to_string

from project.main.models import CustomUser, Page, Plant
from project.main.models import get_default_page

register = template.Library()


def render_menu_tree(user, current_page_id):
    site_homepage = get_default_page()

    try:
        user = CustomUser.objects.get(id=user, is_active=True)
    except CustomUser.DoesNotExist:
        user = AnonymousUser()

    try:
        current = Page.objects.get(id = current_page_id)
    except Page.DoesNotExist:
        current = site_homepage

    if user.is_authenticated and user.permissions.can_manage_plants:
        plants = Plant.objects.all().order_by("order")
    else:

        query = Q(public=True)
        if user.is_authenticated:
            query |= Q(admins__in=[user]) | Q(users__in=[user])
        plants = Plant.objects.filter(query).distinct().order_by("order")

    path = current.traverse_to_root()
    plant_pages = []
    plant_page_ids = []

    def render_name(page, is_plant_root, current = None):
        a_class = []
        if is_plant_root:
            a_class.append("plant_root")
        if current is not None and page == current:
            a_class.append("active")

        if len(a_class) != 0:
            a_class = ' class="%s"' % " ".join(a_class)
        else:
            a_class = ""

        return f'<a href="{page.get_link()}"{a_class}>{page.format_name()}</a>'

    def add_admin_children(path, tree, page):
        tree.append(render_name(page, page.parent_id == 0, current))
        if page in path or page == current:
            t = []
            for p in page.get_children():
                add_admin_children(path, t, p)
            if len(t) != 0:
                tree.append(t)

    def add_children(path, tree, page):
        if page.id not in plant_page_ids:
            if page.can_user_access(user):
                tree.append(render_name(page, page.parent_id == 0, current))
                plant_page_ids.append(page.id)
                parent_added = True
            else:
                parent_added = False

            t = []
            if page in path or not parent_added:
                for p in page.get_children():
                    add_children(path, t, p)

            if len(t) != 0:
                if parent_added:
                    tree.append(t)
                else:
                    for item in t:
                        tree.append(item)

    for plant in plants:
        if (
            (user.is_authenticated and user.is_admin()) or
            plant.is_user_plant_admin(user)
        ):
            add_admin_children(path, plant_pages, plant.homepage)
        else:
            if plant.homepage.can_user_access(user):
                add_children(path, plant_pages, plant.homepage)

    # common site pages
    site_pages = [render_name(site_homepage, False)]

    def add_children(path, tree, page):
        tree.append(render_name(page, False, current))
        if page in path:
            t = []
            for p in page.get_children():
                add_children(path, t, p)
            if len(t) != 0:
                tree.append(t)

    for p in site_homepage.get_children():
        add_children(path, site_pages, p)

    return render_to_string(
        "base/page_tree.html",
        {
            "plant_pages": plant_pages,
            "site_pages": site_pages,
        }
    )


render_menu_tree = stringfilter(render_menu_tree)
register.filter("render_menu_tree", render_menu_tree)
