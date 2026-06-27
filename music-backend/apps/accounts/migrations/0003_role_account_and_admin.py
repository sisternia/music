# Generated manually to link accounts to roles and seed the admin account.

from django.contrib.auth.hashers import make_password
import django.db.models.deletion
from django.db import migrations, models


def create_admin_account(apps, schema_editor):

    Account = apps.get_model("accounts", "Account")
    RoleAccount = apps.get_model("roles_permissions", "RoleAccount")

    admin_role = RoleAccount.objects.get(role_code="ADMIN")

    Account.objects.get_or_create(
        user_id=0,
        defaults={
            "email": "admin@harmonyaiinc.com",
            "password": make_password("123456Ha#"),
            "role_id": admin_role.role_id,
        },
    )


def delete_admin_account(apps, schema_editor):

    Account = apps.get_model("accounts", "Account")
    Account.objects.filter(user_id=0).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_verifyaccount"),
        ("roles_permissions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="role",
            field=models.ForeignKey(
                db_column="role_id",
                default=2,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="accounts",
                to="roles_permissions.roleaccount",
            ),
        ),
        migrations.RunPython(create_admin_account, delete_admin_account),
    ]
