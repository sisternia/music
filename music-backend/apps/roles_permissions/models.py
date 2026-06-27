from django.db import models


class RoleAccount(models.Model):

    class RoleCode(models.TextChoices):
        ADMIN = "ADMIN", "ADMIN"
        USER = "USER", "USER"

    role_id = models.BigAutoField(
        primary_key=True
    )

    role_code = models.CharField(
        max_length=20,
        unique=True,
        choices=RoleCode.choices,
    )

    role_name = models.CharField(
        max_length=50
    )

    create_time = models.DateTimeField(
        auto_now_add=True
    )

    update_time = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "role_account"

    def __str__(self):
        return self.role_code
