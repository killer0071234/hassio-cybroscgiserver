from django.core.management import BaseCommand

from project.main.report import create_alarms_report


class Command(BaseCommand):
    def handle(self, *args, **options):
        create_alarms_report()
