from django.core.management.base import BaseCommand

from project.main.report import send_alarms_report


class Command(BaseCommand):
    def handle(self, *args, **options):
        send_alarms_report()
