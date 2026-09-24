from rest_framework import serializers


class UserDisplaySerializer(serializers.Serializer):

    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    role_id = serializers.IntegerField(allow_null=True)
    role_code = serializers.CharField(allow_null=True)
    role_name = serializers.CharField(allow_null=True)
    verify_status = serializers.CharField(allow_null=True)
    create_time = serializers.DateTimeField()
    update_time = serializers.DateTimeField()
