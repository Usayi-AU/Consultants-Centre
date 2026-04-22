from django.core.management import call_command
from django.core.management.base import BaseCommand

from reports.models import ClientReport


class Command(BaseCommand):
    help = "Seed tracker data only when ClientReport is empty."

    def handle(self, *args, **options):
        if ClientReport.objects.exists():
            self.stdout.write(self.style.WARNING("Skipping seed: ClientReport already has data."))
            return

        self.stdout.write("No report records found. Importing tracker workbook...")
        call_command("import_tracker")
        self.stdout.write(self.style.SUCCESS("Initial tracker data seeded."))