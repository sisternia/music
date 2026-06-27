from django.db import models


class Account(models.Model):
    user_id = models.BigAutoField(
        primary_key=True
    )

    email = models.EmailField(
        unique=True
    )

    password = models.CharField(
        max_length=255
    )

    role = models.ForeignKey(
        "roles_permissions.RoleAccount",
        on_delete=models.PROTECT,
        db_column="role_id",
        related_name="accounts",
        default=2,
    )

    create_time = models.DateTimeField(
        auto_now_add=True
    )

    update_time = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "account"


class VerifyAccount(models.Model):

    class VerifyStatus(models.TextChoices):
        UNVERIFIED = "UNVERIFIED", "UNVERIFIED"
        VERIFIED = "VERIFIED", "VERIFIED"
        LOCKED = "LOCKED", "LOCKED"

    verify_id = models.BigAutoField(
        primary_key=True
    )

    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="verify_accounts",
    )

    verify_code = models.CharField(
        max_length=6
    )

    verify_status = models.CharField(
        max_length=20,
        choices=VerifyStatus.choices,
        default=VerifyStatus.UNVERIFIED,
    )

    create_time = models.DateTimeField(
        auto_now_add=True
    )

    verify_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    lock_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "verify_account"
