from datetime import date

from django.db import migrations
from django.db.models import Q


Q3_START = date(2026, 7, 1)


def oct(day):
    return date(2026, 10, day)


def nov(day):
    return date(2026, 11, day)


# Q3 operations allocation: operations person -> {client name: due date}.
Q3_OPERATIONS = {
    "Edelbert": {
        "Zimasco Pension Fund": oct(29),
        "Astra Industries PF": oct(26),
        "Brands Africa": nov(3),
        "TRB": oct(27),
        "Vivo Energy": oct(28),
        "FCB PF (formerly Barclays PF)": oct(6),
        "Hippo": oct(13),
        "Mimosa Mining PF": oct(8),
        "TIMB Pension Fund": oct(30),
        "Triangle PF - The Money Plan": oct(14),
        "Triangle Senior Staff": oct(7),
        "CIPF": oct(23),
        "FBC": oct(16),
        "Stanbic": oct(15),
        "The Joseph Pension Fund": oct(21),
        "Zambezi River Authority": nov(4),
        "Zimnat Funds": nov(7),
        "Econet": nov(2),
        "Falcon College PF": oct(5),
        "Girls College": oct(22),
        "Minerva Income Withdrawal Fund": oct(19),
        "Minerva Umbrella Fund": oct(20),
        "Unicem PF (Actives)": oct(9),
        "Unicem PF (Pensioners)": oct(12),
    },
    "Isaac": {
        "Seedco": oct(5),
        "Allied Timbers": oct(26),
        "Zimplow": nov(3),
        "MCAZ": oct(6),
        "NBS": oct(28),
        "Fintrust - Risk": oct(27),
        "Petrotrade Pension Fund": oct(13),
        "CAAZ": oct(23),
        "Innscor Pension Fund": oct(7),
        "Investor Protection Fund - Investments": oct(14),
        "Investor Protection Fund - Risk": oct(7),
        "NSSA": oct(8),
        "Simbisa": oct(16),
        "BOC Pension Fund": oct(15),
        "Dairibord": oct(21),
        "Shamwa Gold Mine": nov(4),
        "Stanchart Pension Fund": oct(30),
        "Zimnat Group Staff PF": nov(2),
        "Zimsec Pension Fund": oct(5),
        "Edgars Actives PF": oct(22),
        "Edgars Pensioners PF": oct(19),
        "Minerva Copvol PF": oct(20),
        "Minerva Risk Advisors": oct(9),
        "Nestle": oct(12),
    },
    "Simba": {
        "AGS": oct(5),
        "Getbucks": oct(26),
        "Telecel": nov(3),
        "Marsh Employees PF": oct(6),
        "Sandvik Pension Fund": oct(28),
        "St Johns": oct(27),
        "BPB Gypsum / Saint Gobain": oct(13),
        "Shangani Holistic": oct(5),
        "EY Pension Fund": oct(21),
        "ABC": oct(14),
        "Mashonaland Tobacco Company": oct(7),
        "NOIC Pension Fund": oct(8),
        "Unilever Zimbabwe PF": oct(16),
        "United Refineries": oct(15),
        "Freda Rebecca": oct(7),
        "Goldridge": nov(4),
        "IDBZ": oct(30),
        "Larfarge PF (Actives)": oct(22),
        "Larfarge PF (Pensioners)": oct(23),
        "PSMAS": nov(2),
        "Masiyephambili Schools Trust PF": oct(19),
        "Mimosa Corporate Funds": oct(20),
        "Minerva Provident": oct(9),
        "Whitestone School Trust PF": oct(12),
    },
}


def forwards(apps, schema_editor):
    ClientReport = apps.get_model("reports", "ClientReport")
    SharePointTrackerEntry = apps.get_model("reports", "SharePointTrackerEntry")

    for operations_assignee, clients in Q3_OPERATIONS.items():
        for client_name, due_date in clients.items():
            reports = ClientReport.objects.filter(quarter="q3", client_name=client_name)
            reports.update(operations_assignee=operations_assignee)
            # Only replace due dates still carried over from Q1; keep dates the team has already set.
            reports.filter(Q(due_date__isnull=True) | Q(due_date__lt=Q3_START)).update(due_date=due_date)

    for model in (ClientReport, SharePointTrackerEntry):
        model.objects.filter(client_name="Zimnat Funds").update(crm_name="Tatenda")


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0020_apply_client_crm_allocations"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
