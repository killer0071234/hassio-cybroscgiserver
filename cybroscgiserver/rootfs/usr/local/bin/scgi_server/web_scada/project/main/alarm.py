import datetime
import math

import pytz
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from settings import settings
from project.main.models import Alarm, Controller, Plant
from project.main.util import nad_str_to_nad, localize_timestamp


def get_alarm_list(plant_id, nad, filter_type, filter_activity,
                   items_per_page, page_index):
    nad = nad_str_to_nad(nad)

    try:
        items_per_page = int(items_per_page)
        page_index = int(page_index)
    except (AttributeError, ValueError):
        items_per_page = 10
        page_index = 0

    filters_type = ["all", "alarms", "events"]

    try:
        filter_type_index = filters_type.index(filter_type)
    except ValueError:
        filter_type_index = 0

    start_index = page_index * items_per_page
    end_index = (page_index + 1) * items_per_page

    if nad == 0:
        # get alarms for whole plant
        try:
            plant = Plant.objects.get(id=plant_id)
        except Plant.DoesNotExist:
            return [], 0

        controllers = [c.nad for c in Controller.objects.filter(plant=plant)]
        items = Alarm.objects.filter(nad__in=controllers)
    else:
        items = Alarm.objects.filter(nad=nad)

    if filter_type != "all":
        items = items.filter(type=filter_type_index)

    if filter_activity == "active":
        items = items.filter(timestamp_gone=None) | \
                items.filter(timestamp_gone__day=0)
    elif filter_activity == "waiting_ack":
        items = items.filter(timestamp_ack=None) | \
                items.filter(timestamp_ack__day=0)

    total_items_count = items.count()
    items = items.order_by("-timestamp_raise")[start_index:end_index]

    return items, total_items_count


def get_alarms(request, plant_id, nad, filter_type, filter_activity,
               items_per_page, page_index, rw_access, download_btn):
    rw_access = rw_access == "1"
    download_btn = download_btn == "1"
    items_per_page = int(items_per_page)
    page_index = int(page_index)
    
    plant = Plant.objects.get(id=plant_id)
    timezone = "UTC"
    if plant:
        timezone = plant.timezone
        
    (items, total_items_count) = get_alarm_list(
        plant_id, nad, filter_type, filter_activity, items_per_page,
        page_index
    )

    for item in items:
        classes = []
        item.active = item.timestamp_gone is None
        item.ack_enabled = item.type == 1 and item.timestamp_ack is None
        item.timezone = timezone

        if item.type == 1:
            classes.append("alarm")
        else:
            classes.append("event")

        if item.active:
            classes.append("active")

        if item.type == 1:
            if item.ack_enabled:
                classes.append("not_ack")
            else:
                classes.append("ack")

        item.classes = " ".join(classes)

    page_count = math.ceil(total_items_count / items_per_page)
    next_enabled = page_index > 0
    prev_enabled = page_index < page_count

    return render(
        request,
        "objects/alarm_list_contents.html",
        {
            "items" : items,
            "recent_enabled": True,
            "prev_enabled": prev_enabled,
            "next_enabled": next_enabled,
            "page_index": page_index,
            "page_count": page_count,
            "pages": range(1, page_count + 2),
            "prev_page": page_index + 1,
            "next_page": page_index - 1,
            "rw_access": rw_access,
            "download_btn": download_btn,
            "filter_type": filter_type,
            "filter_activity": filter_activity,
        }
    )


def download_alarms(request, plant_id, nad, filter_type, filter_activity,
                    items_per_page, page_index):
    try:
        items_per_page = int(items_per_page)
        page_index = int(page_index)
    except:
        items_per_page = 10
        page_index = 0
        
    plant = Plant.objects.get(id=plant_id)
    timezone = "UTC"
    if plant:
        timezone = plant.timezone

    (items, total_items_count) = get_alarm_list(
        plant_id, nad, filter_type, filter_activity, items_per_page,
        page_index
    )

    data = ["type;raised;gone;tag;message;status;ack"]
    fname = "alarms_c%s_%s.csv" % (nad, datetime.datetime.now().date())

    for item in items:
        classes = []
        item.active = item.timestamp_gone == None
        item.ack_enabled = item.type == 1 and item.timestamp_ack == None
        item.timezone = timezone
        s = ""

        type = "alarm" if item.type == 1 else "event"
        gone = localize_timestamp(item.timestamp_gone) \
            if item.timestamp_gone is not None \
            else "still active"
        status = "gone" if item.timestamp_gone is not None else "still active"

        if item.type == 1:
            ack = localize_timestamp(item.timestamp_ack) \
                if item.timestamp_ack is not None \
                else "not acknowledged"
        else:
            ack = ""

        s += (f"{type};{localize_timestamp(item.timestamp_raise)};"
              f"{gone};{item.tag};{item.message};{status};{ack}")

        if item.active:
            classes.append("active")

        if item.type == 1:
            if item.ack_enabled:
                classes.append("not_ack")
            else:
                classes.append("ack")

        data.append(s)

    data = "\n".join(data)
    
    if settings.CSV_EXPORT_CHARSET is not None:
        data = data.encode(settings.CSV_EXPORT_CHARSET)
    
    response = HttpResponse(data, content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={fname}"
    return response


@login_required
def ack_alarm(request, id):
    try:
        alarm = Alarm.objects.get(id=id)
        
        controller = Controller.objects.get(nad=alarm.nad)
        try:
            tz = pytz.timezone(controller.plant.timezone)
        except:
            tz = pytz.utc

        # get controller timezone and calc localtime for controller from UTC
        now = datetime.datetime.now(pytz.utc)
        rtv = now.astimezone(tz)
        # delete timezone info in datetime object because mysql cannot handle
        # it
        now = now.replace(tzinfo=None)

        alarm.timestamp_ack = now
        alarm.save()

        return HttpResponse(rtv.strftime("%Y-%m-%d %H:%M:%S"))
    except:
        raise
