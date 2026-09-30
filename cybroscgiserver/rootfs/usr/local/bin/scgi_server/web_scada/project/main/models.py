import os
import shutil
from typing import Optional, List

from django.contrib.auth.models import User, UserManager
from django.core.cache import cache
from django.db import models, connection
from django.template.defaultfilters import slugify

import settings.settings
from project.main.util import localize_timestamp_with_zone, localize_timestamp


def get_default_page():
    try:
        return Page.objects.get(id=1)
    except Page.DoesNotExist:
        return None


class CustomUser(User):
    name = models.CharField(max_length=50, blank=True)
    creator = models.ForeignKey("CustomUser", blank=True, null=True,
                                on_delete=models.SET_NULL)
    login_count = models.IntegerField(default=0)
    permissions = models.OneToOneField("UserPermissions", unique=True,
                                       on_delete=models.DO_NOTHING)
    subscriptions = models.OneToOneField("UserSubscriptions", unique=True,
                                         on_delete=models.DO_NOTHING)
    last_ip = models.GenericIPAddressField(default="")
    homepages = models.ManyToManyField("Page", blank=True)

    # Use UserManager to get the create_user method, etc.
    objects = UserManager()

    class Meta:
        db_table = 'users'

    _homepages_set = None
    _is_plant_admin: Optional[dict] = None

    def __str__(self):
        return f"[{self.id:05d}] {self.username} ({self.email})"

    def is_admin(self):
        return self.is_superuser or self.is_staff

    def format_name(self):
        if len(self.name) != 0:
            return self.name
        else:
            return self.username

    def get_all_pages(self):
        def read_child(page_id, plant_obj):
            r = []
            pages = Page.objects.filter(parent__id=page_id).order_by("order")

            for pg in pages:
                if pg not in self.homepages.all():
                    pg.plant = plant_obj
                    r.append(pg)
                    r += read_child(pg.id, plant_obj)
            return r

        res = []
        for p in self.homepages.all().order_by("order"):
            plant = p.get_plant()
            p.plant = plant
            res += [p] + read_child(p.id, plant)

        return res

    def get_all_site_pages(self):
        site_homepage = get_default_page()
        return [site_homepage] + site_homepage.get_descendants()

    def get_all_plants_pages(self):
        res = []

        if self.permissions.can_manage_plants:
            plants = Plant.objects.all()
            for plant in plants:
                res += [plant.homepage] + plant.homepage.get_descendants()
        else:
            plants = Plant.objects.filter(admins__in=[self])
            for plant in plants:
                res += [plant.homepage] + plant.homepage.get_descendants()

            for p in self.homepages.all():
                if p not in res:
                    res += [p] + p.get_descendants()

        return res

    def is_homepage(self, page):
        if self.id != 0:
            return self.homepages.filter(id__in=[page.id]).count() != 0
        else:
            return False

    def delete(self, using=None, keep_parents=False):
        # break relations
        self.permissions.delete()
        Relay.objects.filter(user=self).delete()
        super().delete(using, keep_parents)

    def is_any_plant_admin(self) -> bool:
        return Plant.objects.filter(admins__in=[self]).count() != 0

    def is_plant_admin(self, plant) -> bool:
        if plant is not None:
            if self._is_plant_admin is None:
                self._is_plant_admin = {}

            if plant.id in self._is_plant_admin:
                return self._is_plant_admin[plant.id]

            value = plant.admins.filter(id__in=[self.id]).count() != 0
            self._is_plant_admin.update({plant.id: value})

            return value
        else:
            return False

    def can_manage_plant(self, plant):
        return self.permissions.can_manage_plants or self.is_plant_admin(plant)

    def can_manage_plants(self):
        return self.permissions.can_manage_plants or self.is_any_plant_admin()

    def get_homepages_set(self):
        if self._homepages_set is None:
            ids = []
            for p in self.homepages.all():
                ids.append(p.id)
            self._homepages_set = set(ids)
        return self._homepages_set

    def has_rw_access(self, page: "Page") -> bool:
        rw_access = self.is_authenticated and self.permissions.rw_tags_access

        if self.permissions.is_server_admin:
            return True
        elif rw_access:
            plant = page.get_plant()

            return plant is not None and (
                self.is_plant_admin(plant) or
                plant.is_user_plant_user(self)
            )
        else:
            return False

    def get_descendants(self):
        def get_child_nodes(node):
            res = []
            for p in (
                CustomUser
                    .objects
                    .filter(creator=node, is_active=True)
                    .order_by("username")
            ):
                res.append(p)
                res += get_child_nodes(p)
            return res

        return get_child_nodes(self)

    def get_all_accessible_users(self):
        if (
            self.permissions.is_server_admin and
            self.permissions.can_manage_users
        ):
            return [
                p for p in
                CustomUser.objects.filter(is_active=True).order_by("username")
            ]
        else:
            return self.get_descendants()


class UserPermissions(models.Model):
    id = models.AutoField(primary_key=True)
    is_server_admin = models.BooleanField(default=False)
    can_manage_site_content = models.BooleanField(default=False)
    can_manage_plants = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_templates = models.BooleanField(default=False)
    can_manage_controllers = models.BooleanField(default=False)
    can_manage_media = models.BooleanField(default=False)
    rw_tags_access = models.BooleanField(default=False)

    class Meta:
        db_table = 'permissions'

    def set_admin_permissions(self):
        self.is_server_admin = True
        self.can_manage_site_content = True
        self.can_manage_plants = True
        self.can_manage_users = True
        self.can_manage_templates = True
        self.can_manage_controllers = True
        self.can_manage_media = True
        self.rw_tags_access = True

    def get_str(self):
        res = ""
        if self.is_server_admin:
            res += "A"
        if self.can_manage_users:
            res += "U"
        if self.can_manage_controllers:
            res += "C"
        if self.can_manage_templates:
            res += "T"
        if self.can_manage_media:
            res += "M"
        if self.can_manage_site_content:
            res += "S"
        if self.can_manage_plants:
            res += "P"
        if self.rw_tags_access:
            res += "W"
        return res if len(res) != 0 else "-"

    def has_any_permission(self):
        return self.get_str() != "-"


class UserSubscriptions(models.Model):
    id = models.AutoField(primary_key=True)
    alarms_events_subscription = models.BooleanField(default=False)

    class Meta:
        db_table = 'subscriptions'


class Plant(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    author = models.ForeignKey("CustomUser", related_name="author", blank=True,
                               null=True, on_delete=models.SET_NULL)
    modified_by = models.ForeignKey("CustomUser",
                                    related_name="plant_modified_by",
                                    blank=True, null=True,
                                    on_delete=models.SET_NULL)
    order = models.IntegerField(default=0)
    homepage = models.ForeignKey("Page", related_name="plant_homepage",
                                 blank=True, null=True,
                                 on_delete=models.SET_NULL)
    public = models.BooleanField(default=False)
    admins = models.ManyToManyField("CustomUser", related_name="plant_admins")
    users = models.ManyToManyField("CustomUser", related_name="plant_users")
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    timezone = models.CharField(max_length=64)

    class Meta:
        db_table = 'plants'
        ordering = ["order"]

    def __str__(self):
        return f"[{self.id:5d}] {self.format_name()}"

    def format_name(self):
        return self.name if len(self.name) != 0 else "[ no name ]"

    def get_all_pages(self):
        return [self.homepage] + self.homepage.get_descendants()

    def get_absolute_data_path(self):
        return settings.settings.DATA_FOLDER_ROOT + self.homepage.data_folder \
            if self.homepage else ""

    def is_user_plant_admin(self, user):
        return user.is_authenticated and user.is_plant_admin(self)

    def is_user_plant_user(self, user):
        return user.is_authenticated and self.users.filter(
            id__in=[user.id]).count() != 0

    def can_user_manage_content(self, user):
        return user.is_admin() or self.is_user_plant_admin(user)

    def delete(self, using=None, keep_parents=None):
        # unassign all controllers
        Controller.objects.filter(plant=self).update(plant=None)

        path = os.path.normpath(self.get_absolute_data_path())
        if len(path) != 0 and path != os.path.normpath(
            settings.settings.DATA_FOLDER_ROOT
        ):
            try:
                shutil.rmtree(path)
            except:
                pass

        if self.homepage:
            self.homepage.delete()

        super().delete(using, keep_parents)

        Plant().normalize_order()

    @staticmethod
    def normalize_order():
        for n, plant in enumerate(Plant.objects.all()):
            plant.order = n
            plant.save()

    def user_has_rw_access(self, user) -> bool:
        rw_access = user.is_authenticated and user.permissions.rw_tags_access

        if rw_access:
            rw_access = user.is_plant_admin(self) or self.is_user_plant_user(
                user)

        return rw_access


class Controller(models.Model):
    id = models.AutoField(primary_key=True)
    nad = models.CharField(max_length=12, blank=False, null=False)
    location = models.CharField(max_length=50, blank=True)
    function = models.CharField(max_length=1000, blank=True)
    created = models.ForeignKey("CustomUser", related_name="created",
                                blank=True, null=True,
                                on_delete=models.SET_NULL)
    owner = models.ForeignKey("CustomUser", related_name="owner", blank=True,
                              null=True, on_delete=models.SET_NULL)
    plant = models.ForeignKey("Plant", related_name="plant", blank=True,
                              null=True, on_delete=models.SET_NULL)
    active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'controllers'

    def __str__(self):
        return self.nad


class Page(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    parent = models.ForeignKey("Page", null=True, blank=True, default=None,
                               on_delete=models.SET_NULL)
    plant = models.ForeignKey("Plant", null=True, blank=True, default=None,
                              on_delete=models.SET_NULL)
    path = models.CharField(max_length=200)
    data_folder = models.CharField(max_length=200, default="")
    content = models.TextField(blank=True)
    author = models.ForeignKey("CustomUser", blank=True, null=True,
                               on_delete=models.SET_NULL)
    modified_by = models.ForeignKey("CustomUser",
                                    related_name="page_modified_by",
                                    blank=True, null=True,
                                    on_delete=models.SET_NULL)
    order = models.IntegerField(default=0)
    update_period = models.ForeignKey("UpdatePeriod", blank=True, null=True,
                                      on_delete=models.SET_NULL)
    public = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pages'

    traverse_to_root_path: List['Page'] = None
    _plant: Optional[Plant] = None

    def __str__(self):
        return f"[{self.id:5d}] {self.format_name()}"

    def format_name(self):
        return self.name if len(self.name) != 0 else "[ no name ]"

    def get_link(self):
        return "/p/%s/%d/" % (slugify(self.name), self.id)

    def get_list_indent(self):
        return "&nbsp;&nbsp;&nbsp;&nbsp;" * self.get_parent_count()

    def get_list_indent_px(self):
        return 20 * self.get_parent_count()

    def get_parent_count(self):
        parent_count = 0
        p_id = self.parent_id
        finished = False

        while not finished:
            if p_id is not None:
                pages = Page.objects.filter(id=p_id).values("parent_id")
                if len(pages) > 0:
                    p_id = pages[0]["parent_id"]
                    parent_count += 1
                else:
                    finished = True
            else:
                finished = True

        return parent_count

    def get_children(self):
        return (
            Page
            .objects
            .filter(parent=self, published=True)
            .order_by("order")
        )

    def get_descendants(self):
        def get_child_nodes(node):
            res = []
            for p in Page.objects.filter(parent=node).order_by("order"):
                res.append(p)
                res += get_child_nodes(p)
            return res

        return get_child_nodes(self)

    def get_siblings_with_self(self):
        return Page.objects.filter(parent__id=self.parent_id).order_by("order")

    def get_siblings(self):
        return self.get_siblings_with_self().exclude(id=self.id)

    def get_all_pages_except_this(self):
        def read_child(page_id):
            r = []
            pages = (
                Page
                .objects
                .filter(parent__id=page_id)
                .exclude(id=self.id)
                .order_by("order")
            )

            for pg in pages:
                r.append(pg)
                r += read_child(pg.id)
            return r

        res = []
        for p in self.author.homepages.all():
            res.append(p)
            res += read_child(p.id)

        return res

    def traverse_to_root(self) -> List['Page']:
        if self.traverse_to_root_path is None:
            p = self
            res: List['Page'] = []

            while p.id is not None:
                res += [p]
                if p.parent is not None:
                    try:
                        p = Page.objects.get(id=p.parent.id)
                    except Page.DoesNotExist:
                        break
                else:
                    break

            res.reverse()
            for level, p in enumerate(res):
                p.level = level

            self.traverse_to_root_path = res

        return self.traverse_to_root_path

    def get_full_path(self) -> str:
        p = self
        res: List[str] = []

        while p.id != 0:
            res += [p.name]
            if p.parent is None:
                break

            try:
                p = Page.objects.get(id=p.parent.id)
            except Page.DoesNotExist:
                break

        res.reverse()

        for i in range(len(res)):
            res[i] = slugify(res[i])

        path = ".".join(res).lower()

        return path

    def get_data_folder(self):
        path = self.traverse_to_root()
        path.reverse()

        for p in path:
            if len(p.data_folder) != 0:
                return p.data_folder

        return ""

    def get_dedicated_data_folder(self):
        path = self.get_full_path()
        path = path.replace(".", "/") + "/"
        return path

    def get_plant(self) -> Optional[Plant]:
        if self._plant is None:
            tree = self.traverse_to_root()
            if len(tree) != 0:
                try:
                    self._plant = Plant.objects.get(homepage=tree[0])
                except Plant.DoesNotExist:
                    return None
        return self._plant

    def can_user_access(self, user):
        if not self.published:
            return False

        plant = self.get_plant()
        is_site_page: bool = plant is None

        if user.is_authenticated:
            path = self.traverse_to_root()
            path_ids = [p.id for p in path]
            is_homepage_in_path = len(
                set(path_ids).intersection(user.get_homepages_set())) != 0
        else:
            is_homepage_in_path = False

        return self.published and (
            is_site_page or
            self.public or
            user.is_authenticated and (
                user.is_admin() or
                plant.is_user_plant_admin(user) or
                is_homepage_in_path
            )
        )

    def can_user_edit(self, user) -> bool:
        plant = self.get_plant()
        is_site_page: bool = plant is None

        return user.is_authenticated and (
            user.permissions.is_server_admin or (
                not is_site_page and (
                    user.permissions.can_manage_plants or
                    user.is_plant_admin(plant)
                )
            )
        )

    def delete(self, using=None, keep_parents=False):
        for p in Page.objects.filter(parent=self):
            p.delete()
        return super().delete(using, keep_parents)

    def get_cache_key(self) -> str:
        return f"page_{self.id}"

    def delete_cache(self):
        cache.delete(self.get_cache_key())


class Template(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    author = models.ForeignKey("CustomUser", blank=True, null=True,
                               on_delete=models.SET_NULL)
    modified_by = models.ForeignKey("CustomUser",
                                    related_name="template_modified_by",
                                    blank=True, null=True,
                                    on_delete=models.SET_NULL)
    order = models.IntegerField(default=0)
    published = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'templates'
        ordering = ["order"]

    def __str__(self):
        return f"[{self.id:5d}] {self.name}"

    def format_name(self):
        return self.name if len(self.name) != 0 else "[ no name ]"

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # delete all cached data
        cache_path = os.path.normpath(settings.settings.CACHE_ROOT)
        try:
            shutil.rmtree(cache_path)
        except:
            pass
        super().save(force_insert, force_update, using, update_fields)

    def normalize_order(self):
        for n, item in enumerate(Template.objects.all()):
            item.order = n
            item.save()

    def delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)
        self.normalize_order()


class Measurement(models.Model):
    id = models.AutoField(primary_key=True)
    nad = models.CharField(max_length=12, null=False)
    tag = models.CharField(max_length=40, null=False)
    value = models.CharField(max_length=16, null=False)
    timestamp = models.DateTimeField(null=False)

    class Meta:
        db_table = 'measurements'

    def __str__(self):
        return f"[{self.id:5d}] {self.timestamp} {self.tag} = {self.value}"


class Alarm(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.IntegerField(default=0, null=False)
    nad = models.CharField(max_length=12, null=False)
    tag = models.CharField(max_length=40, null=False)
    value = models.CharField(max_length=16, null=False)
    priority = models.SmallIntegerField(default=0, null=False)
    alarm_class = models.CharField(
        max_length=20, db_column="class", null=False
    )
    message = models.CharField(max_length=50, null=False)
    timestamp_raise = models.DateTimeField(blank=True, null=False)
    timestamp_gone = models.DateTimeField(blank=True, null=True)
    timestamp_ack = models.DateTimeField(blank=True, null=True)

    def get_local_timestamp_raise(self):
        return localize_timestamp(self.timestamp_raise)

    def get_local_timestamp_gone(self):
        return localize_timestamp(self.timestamp_gone)

    def get_local_timestamp_ack(self):
        return localize_timestamp(self.timestamp_ack)

    class Meta:
        db_table = 'alarms'


class PlantReport:
    def __init__(self, plant_id, report_id, report_type, timestamp_from,
                 timestamp_to):
        self.plant_id = plant_id
        self.report_id = report_id
        self.report_type = report_type
        self.timestamp_from = timestamp_from
        self.timestamp_to = timestamp_to
        self.alarms = []
        self.timezone = None

    def get_local_timestamp_from(self):
        return localize_timestamp_with_zone(self.timezone, self.timestamp_from)

    def get_local_timestamp_to(self):
        return localize_timestamp_with_zone(self.timezone, self.timestamp_to)


class AlarmReport:
    def __init__(self, plant_report, alarm_id, nad, alarm_type, tag, value,
                 alarm_class, message, timestamp_raise, timestamp_gone,
                 timestamp_ack):
        self.plant_report = plant_report
        self.alarm_id = alarm_id
        self.nad = nad
        self.alarm_type = alarm_type
        self.tag = tag
        self.value = value
        self.alarm_class = alarm_class
        self.message = message
        self.timestamp_raise = timestamp_raise
        self.timestamp_gone = timestamp_gone
        self.timestamp_ack = timestamp_ack

    def get_max_timestamp(self):
        tss = []
        if self.timestamp_raise:
            tss.append(self.timestamp_raise)
        if self.timestamp_gone:
            tss.append(self.timestamp_gone)
        if self.timestamp_ack:
            tss.append(self.timestamp_ack)
        if tss:
            return max(tss)
        return None

    def get_local_timestamp_raise(self):
        return localize_timestamp_with_zone(self.plant_report.timezone,
                                            self.timestamp_raise)

    def get_local_timestamp_gone(self):
        return localize_timestamp_with_zone(self.plant_report.timezone,
                                            self.timestamp_gone)

    def get_local_timestamp_ack(self):
        return localize_timestamp_with_zone(self.plant_report.timezone,
                                            self.timestamp_ack)

    def get_changes(self):
        changes = []
        if self.plant_report.timestamp_from and self.plant_report.timestamp_to:
            if (
                self.timestamp_raise and
                self.plant_report.timestamp_from <
                self.timestamp_raise <=
                self.plant_report.timestamp_to
            ):
                changes.append("raised")

            if (
                self.timestamp_gone and
                self.plant_report.timestamp_from <
                self.timestamp_gone <=
                self.plant_report.timestamp_to
            ):
                changes.append("gone")

            if (
                self.timestamp_ack and
                self.plant_report.timestamp_from <
                self.timestamp_ack <=
                self.plant_report.timestamp_to
            ):
                changes.append("acknowledged")

        return ", ".join(changes)


# GK 23.08.2028: below query optimized by Patrik Vinovrski
class ReportManager(models.Manager):
    def new_report_data(self, upper_alarm_timestamp):
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                p.id AS plant_id,
                r.id AS report_id,
                r.type,
                r.timestamp,
                c.nad,
                a.id AS alarm_id,
                a.type,
                a.tag,
                a.value,
                a.class,
                a.message,
                a.timestamp_raise,
                a.timestamp_gone,
                a.timestamp_ack
            FROM (SELECT id FROM plants) p
            INNER JOIN controllers c ON (p.id = c.plant_id)
            LEFT OUTER JOIN (
                SELECT
                    r.id,
                    r.plant_id,
                    r.type,
                    r.timestamp
                FROM (
                    SELECT plant_id, type, MAX(timestamp) AS max_timestamp
                    FROM reports
                    GROUP BY plant_id, type
                ) lr
                INNER JOIN reports r ON (
                    r.plant_id = lr.plant_id AND
                    r.type = lr.type AND
                    r.timestamp = lr.max_timestamp
                )
                WHERE r.type = 1
            ) r ON (p.id = r.plant_id)
            LEFT OUTER JOIN alarms a ON (
                c.nad = a.nad AND (
                    (
                        a.timestamp_raise > r.timestamp AND
                        a.timestamp_raise <= %(max_timestamp)s
                    ) OR (
                        a.timestamp_gone > r.timestamp AND
                        a.timestamp_gone <= %(max_timestamp)s
                    ) OR (
                        a.timestamp_ack > r.timestamp AND
                        a.timestamp_ack <= %(max_timestamp)s
                    )
                )
            )
            ORDER BY a.timestamp_raise DESC""",
            {"max_timestamp": upper_alarm_timestamp})

        rtv = {}
        for row in cursor.fetchall():
            if row[0] in rtv.keys():
                plant_report = rtv[row[0]]
            else:
                plant_report = PlantReport(row[0], row[1], row[2], row[3],
                                           upper_alarm_timestamp)
                rtv[row[0]] = plant_report
            if row[5]:
                alarm_report = AlarmReport(
                    plant_report=plant_report,
                    alarm_id=row[5],
                    nad=row[4],
                    alarm_type=row[6],
                    tag=row[7],
                    value=row[8],
                    alarm_class=row[9],
                    message=row[10],
                    timestamp_raise=row[11],
                    timestamp_gone=row[12],
                    timestamp_ack=row[13]
                )
                plant_report.alarms.append(alarm_report)
        return rtv.values()


class Report(models.Model):
    id = models.AutoField(primary_key=True)
    plant = models.ForeignKey("Plant", related_name="reports", blank=True,
                              null=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(blank=True)
    type = models.IntegerField(default=0)
    timestamp_sent = models.DateTimeField(blank=True, null=True)
    report_text = models.TextField(blank=True, null=True)
    report_html = models.TextField(blank=True, null=True)
    objects = ReportManager()

    class Meta:
        db_table = 'reports'


class UpdatePeriod(models.Model):
    id = models.AutoField(primary_key=True)
    text = models.CharField(max_length=10)
    period = models.IntegerField()

    class Meta:
        db_table = 'updateperiods'

    def __str__(self):
        return f"{self.text} ({self.period}s)"

    def get_period_ms(self):
        return self.period * 1000


class Relay(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING)
    enabled = models.BooleanField(default=False)
    session_id = models.IntegerField(default=0)
    message_count_tx = models.IntegerField(default=0)
    message_count_rx = models.IntegerField(default=0)
    last_message = models.DateTimeField(blank=True, null=True)
    last_controller_nad = models.IntegerField(default=0)

    class Meta:
        db_table = 'relays'
