from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_address_proof_user_id_proof"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="household_type",
            field=models.CharField(
                choices=[("bachelor", "Bachelor"), ("family", "Family")],
                default="family",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="FamilyMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("gender", models.CharField(choices=[("male", "Male"), ("female", "Female"), ("other", "Other")], max_length=10)),
                ("relationship", models.CharField(blank=True, max_length=80)),
                ("date_of_birth", models.DateField()),
                ("age", models.PositiveIntegerField(editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "resident",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="family_members",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name", "id"],
            },
        ),
    ]
