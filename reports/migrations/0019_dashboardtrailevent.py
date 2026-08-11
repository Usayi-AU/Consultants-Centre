from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0018_remove_dashboardsettings_last_ips_signed_date_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DashboardTrailEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "dashboard_key",
                    models.CharField(
                        choices=[
                            ("operations", "Operations Dashboard"),
                            ("business_development", "Business Development Dashboard"),
                            ("alternative_investments", "Alternative Investments Dashboard"),
                            ("client_relations", "Client Relations Dashboard"),
                        ],
                        max_length=64,
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("updated", "Updated"),
                            ("status_changed", "Status changed"),
                            ("deleted", "Deleted"),
                            ("archived", "Archived"),
                        ],
                        max_length=32,
                    ),
                ),
                ("section_label", models.CharField(blank=True, max_length=120)),
                ("record_label", models.CharField(blank=True, max_length=255)),
                ("summary", models.CharField(max_length=255)),
                ("details", models.TextField(blank=True)),
                ("actor_label", models.CharField(default="Admin", max_length=120)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
