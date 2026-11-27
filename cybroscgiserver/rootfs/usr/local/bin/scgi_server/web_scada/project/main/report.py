import datetime
import os
import re
from email.mime.image import MIMEImage
from smtplib import SMTPException

import pytz
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.http import HttpResponse
from django.template.loader import render_to_string

from settings import settings
from project.main.models import Plant, Report


def create_alarms_report():
    now = datetime.datetime.now(pytz.utc) - datetime.timedelta(seconds=2)

    plant_reports = Report.objects.new_report_data(now)

    for plant_report in plant_reports:
        plant = Plant.objects.get(id=plant_report.plant_id)
        plant_report.timezone = plant.timezone

        if plant_report.report_id:
            if plant_report.alarms:
                report_text = render_to_string(
                    template_name="report/alarm_report.txt",
                    context={"plant":plant, "alarm_report":plant_report}
                )
                report_html = render_to_string(
                    template_name="report/alarm_report.html",
                    context={"plant":plant, "alarm_report":plant_report}
                )
                report = Report(
                    plant=plant,
                    timestamp=plant_report.timestamp_to,
                    type=1,
                    report_text=report_text,
                    report_html=report_html
                )
                try:
                    report.save()
                except Warning:
                    pass
        else:
            report = Report(
                plant=plant,
                timestamp=now,
                type=1,
                timestamp_sent=now
            )
            try:
                report.save()
            except Warning:
                pass


def send_alarms_report():
    reports = Report.objects.all()
    reports = reports.filter(timestamp_sent=None) | \
              reports.filter(timestamp_sent__day=0)

    notifications = {'null_user': []}
    for report in reports:
        if report.plant.users.count():
            was_added = False
            for user in report.plant.users.all():
                if (
                    (report.type == 1 and
                     user.subscriptions.alarms_events_subscription) and
                    user.email
                ):
                    emails = re.split("[,;: ]", user.email)
                    for email in emails:
                        email = email.strip()
                        if len(email) > 0:
                            if email not in notifications.keys():
                                notifications[email] = []
                            if notifications[email].count(report) == 0:
                                notifications[email].append(report)
                            was_added = True
            if not was_added:
                notifications['null_user'].append(report)
        else:
            notifications['null_user'].append(report)

    def get_id_from_report(x):
        return x.id

    reports_processed_succ = []

    for address in notifications.keys():
        try:
            if not (address == 'null_user'):
                text_content = render_to_string(
                    template_name="report/report_mail.txt",
                    context={"reports":notifications[address]}
                )
                html_content = render_to_string(
                    template_name="report/report_mail.html",
                    context={"reports":notifications[address]}
                )
                msg = EmailMultiAlternatives(
                    settings.REPORT_EMAIL_SUBJECT,
                    text_content,
                    settings.REPORT_FROM_EMAIL,
                    [address]
                )
                msg.mixed_subtype = 'related'
                msg.attach_alternative(html_content, "text/html")
                try:
                    alarm_image_file = open(
                        finders.find('img/ico_exclamation_red.png'), 'rb'
                    )
                    alarm_msg_image = MIMEImage(alarm_image_file.read())
                    alarm_image_file.close()
                    alarm_msg_image.add_header('Content-ID',
                                               '<ico_exclamation_red>')
                    msg.attach(alarm_msg_image)

                    event_image_file = open(
                        finders.find('img/ico_exclamation.png'), 'rb'
                    )
                    event_msg_image = MIMEImage(event_image_file.read())
                    event_image_file.close()
                    event_msg_image.add_header('Content-ID',
                                               '<ico_exclamation>')
                    msg.attach(event_msg_image)
                except:
                    pass
                msg.send(fail_silently=False)
            reports_processed_succ = reports_processed_succ + \
                list(map(get_id_from_report, notifications[address]))
        except SMTPException:
            pass

    now = datetime.datetime.now(pytz.utc)
    now = now.replace(tzinfo=None)

    reports_processed = Report.objects.filter(id__in=reports_processed_succ)
    try:
        reports_processed.update(timestamp_sent=now)
    except Warning:
        pass


def validate_email_addr(email):
    try:
        validate_email.__call__(email)
        return True
    except:
        return False


def test_alarms_report(request):
    errors = []

    if request.method == "POST":
        emails = re.split("[,;: ]",
                          request.POST.get("emails", "").strip())
        for email in emails:
            email = email.strip()
            if validate_email_addr(email):
                try:
                    text_content = render_to_string(
                        template_name="report/test_mail.txt",
                        context={},
                        request=request
                    )
                    html_content = render_to_string(
                        template_name="report/test_mail.html",
                        context={},
                        request=request
                    )
                    msg = EmailMultiAlternatives(
                        settings.REPORT_EMAIL_SUBJECT,
                        text_content,
                        settings.REPORT_FROM_EMAIL,
                        [email.strip()]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send(fail_silently=False)
                    errors.append({"email":email, "error":"OK"})
                except SMTPException as e:
                    errors.append({"email":email, "error":str(e)})
            else:
                errors.append({"email": email, "error": "E-mail syntax error"})
    rtv = "["
    first = True
    for error in errors:
        if not first:
            rtv += ", "
        else:
            first = False
        rtv += f'{ "email": "{error["email"]}", "error": "{error["error"]}" }'
    rtv += "];"
    return HttpResponse(rtv)
