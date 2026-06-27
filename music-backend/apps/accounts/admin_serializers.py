from rest_framework import serializers

from apps.roles_permissions.models import RoleAccount

from .models import Account


class UserDisplaySerializer(serializers.Serializer):

    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    role_id = serializers.IntegerField(allow_null=True)
    role_code = serializers.CharField(allow_null=True)
    role_name = serializers.CharField(allow_null=True)
    create_time = serializers.DateTimeField()
    update_time = serializers.DateTimeField()


class UserDisplayResponseSerializer(serializers.Serializer):

    message = serializers.CharField()
    data = UserDisplaySerializer(many=True)
