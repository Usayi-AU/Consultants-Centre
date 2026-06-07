from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CRMActionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("client_name", models.CharField(max_length=255)),
                ("crm_owner", models.CharField(max_length=120)),
                ("action_item", models.TextField()),
                ("progress_update", models.TextField(blank=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("in_progress", "Work in Progress"), ("completed", "Completed")],
                        default="in_progress",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["client_name", "-updated_at"],
            },
        ),
    ]
