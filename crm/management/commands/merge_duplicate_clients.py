from django.core.management.base import BaseCommand

from crm.models import ActionItem, MeetingLog


MERGE_MAP = {
    "brands": "Brands Africa",
    "brandsafrica": "Brands Africa",
    "caaz": "CAAZ",
    "dairibord": "Dairiboard",
    "dairiboard": "Dairiboard",
    "mcaz": "MCAZ",
    "mca z": "MCAZ",
    "mca z": "MCAZ",
    "masiye": "Masiyebambili",
    "masiyebambili": "Masiyebambili",
    "masiyepambili": "Masiyebambili",
    "mimosa": "Mimosa",
    "nssa": "NSSA",
    "nssapf": "NSSA",
    "saintgobain": "Saint-Gobain",
    "saintgobain": "Saint-Gobain",
    "stgobain": "Saint-Gobain",
    "sandvik": "Sandvik",
    "simbisabrands": "Simbisa",
    "simbisa": "Simbisa",
    "econet": "Econet PF",
    "econetpf": "Econet PF",
    "fcb": "First Capital Bank",
    "firstcapitalbank": "First Capital Bank",
    "goldridgeschools": "Goldridge",
    "goldridge": "Goldridge",
    "hippovalley": "Hippo",
    "hippo": "Hippo",
    "innscorafrica": "Innscor",
    "innscor": "Innscor",
    "minervafund": "Minerva Funds",
    "minervafunds": "Minerva Funds",
    "shanganiholistic": "Shangani Holistics",
    "shanganiholistics": "Shangani Holistics",
    "tongatt": "Tongaat",
    "tongaat": "Tongaat",
}

DELETE_NAMES = {
    "datlabs",
    "harvestcapital",
    "mmcpf",
    "theavenuesclinic",
    "tourismindustrypensionfund",
}


def normalize_name(value):
    if value is None:
        return ""
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum())


class Command(BaseCommand):
    help = "Merge duplicate CRM client names into their canonical client names and delete clearly obsolete entries."

    def handle(self, *args, **options):
        updated = 0
        deleted = 0

        for model in (ActionItem, MeetingLog):
            for record in model.objects.all():
                raw_name = record.client or ""
                normalized = normalize_name(raw_name)
                if not normalized:
                    continue

                if normalized in DELETE_NAMES:
                    record.delete()
                    deleted += 1
                    continue

                canonical = MERGE_MAP.get(normalized)
                if canonical and canonical != raw_name.strip():
                    record.client = canonical
                    record.save(update_fields=["client"])
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Merged {updated} CRM client records and deleted {deleted} obsolete client records."
            )
        )
