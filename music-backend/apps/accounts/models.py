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

    create_time = models.DateTimeField(
        auto_now_add=True
    )

    update_time = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "account"