from django.db import migrations

from reports.crm_allocations import apply_crm_allocations


def forwards(apps, schema_editor):
    apply_crm_allocations(
        apps.get_model("reports", "ClientReport"),
        apps.get_model("reports", "SharePointTrackerEntry"),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0019_dashboardtrailevent"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
