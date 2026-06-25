from rest_framework import serializers

from .models import Account
from .services import EmailValidationService
from .validators import validate_password


class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True
    )


class RegisterSerializer(serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    confirm_password = serializers.CharField(
        write_only=True
    )

    def validate_email(self, value):

        if Account.objects.filter(
            email=value
        ).exists():

            raise serializers.ValidationError(
                "Email already exists."
            )

        if not EmailValidationService.validate(value):

            raise serializers.ValidationError(
                "This email address is invalid."
            )

        return value

    def validate(self, attrs):

        if (
            attrs["password"] !=
            attrs["confirm_password"]
        ):

            raise serializers.ValidationError(
                {
                    "confirm_password":
                    "Passwords do not match."
                }
            )

        return attrs


class SendVerifyCodeSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def validate_email(self, value):

        try:

            self.account = Account.objects.get(
                email=value
            )

        except Account.DoesNotExist:

            raise serializers.ValidationError(
                "Account not found."
            )

        return value


class VerifyCodeSerializer(serializers.Serializer):

    email = serializers.EmailField()

    verify_code = serializers.CharField(
        min_length=6,
        max_length=6,
    )


class ResendVerifyCodeSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def validate_email(self, value):

        try:

            self.account = Account.objects.get(
                email=value
            )

        except Account.DoesNotExist:

            raise serializers.ValidationError(
                "Account not found."
            )

        return value