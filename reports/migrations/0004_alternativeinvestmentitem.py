from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0003_crmactionhistory"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlternativeInvestmentItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("investment_name", models.CharField(max_length=255)),
                ("client_name", models.CharField(blank=True, max_length=255)),
                ("category", models.CharField(blank=True, max_length=120)),
                ("owner", models.CharField(blank=True, max_length=120)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("green", "Green / On Track"),
                            ("amber", "Amber / Watch"),
                            ("red", "Red / Critical"),
                        ],
                        default="green",
                        max_length=20,
                    ),
                ),
                ("summary_update", models.TextField(blank=True)),
                ("detailed_review", models.TextField(blank=True)),
                ("last_update", models.DateField(blank=True, null=True)),
                ("next_review_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["investment_name"],
            },
        ),
    ]