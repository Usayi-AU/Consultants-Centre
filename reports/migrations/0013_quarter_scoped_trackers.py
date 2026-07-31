from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0012_alter_sharepointtrackerentry_status_proposal_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientreport",
            name="quarter",
            field=models.CharField(
                choices=[("q1", "First Quarter"), ("q2", "Second Quarter"), ("q3", "Third Quarter")],
                default="q1",
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name="sharepointtrackerentry",
            name="quarter",
            field=models.CharField(
                choices=[("q1", "First Quarter"), ("q2", "Second Quarter"), ("q3", "Third Quarter")],
                default="q1",
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="clientreport",
            name="client_name",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="sharepointtrackerentry",
            name="client_name",
            field=models.CharField(max_length=255),
        ),
        migrations.AddConstraint(
            model_name="clientreport",
            constraint=models.UniqueConstraint(fields=("quarter", "client_name"), name="unique_report_client_per_quarter"),
        ),
        migrations.AddConstraint(
            model_name="sharepointtrackerentry",
            constraint=models.UniqueConstraint(fields=("quarter", "client_name"), name="unique_sharepoint_client_per_quarter"),
        ),
    ]
