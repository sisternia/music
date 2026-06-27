# Generated manually to add role_account table.

from django.db import migrations, models


def seed_roles(apps, schema_editor):

    RoleAccount = apps.get_model("roles_permissions", "RoleAccount")

    RoleAccount.objects.get_or_create(
        role_code="ADMIN",
        defaults={
            "role_name": "ADMIN",
        },
    )

    RoleAccount.objects.get_or_create(
        role_code="USER",
        defaults={
            "role_name": "USER",
        },
    )


def unseed_roles(apps, schema_editor):

    RoleAccount = apps.get_model("roles_permissions", "RoleAccount")
    RoleAccount.objects.filter(role_code__in=["ADMIN", "USER"]).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RoleAccount",
            fields=[
                ("role_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("role_code", models.CharField(choices=[("ADMIN", "ADMIN"), ("USER", "USER")], max_length=20, unique=True)),
                ("role_name", models.CharField(max_length=50)),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("update_time", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "role_account",
            },
        ),
        migrations.RunPython(seed_roles, unseed_roles),
    ]
