from django.contrib.auth.hashers import check_password, make_password

from drf_yasg.utils import swagger_auto_schema

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    SendVerifyCodeSerializer,
)
from .services import MailService


class LoginView(APIView):

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Login",
        operation_description="Login with email and password",
        request_body=LoginSerializer,
        responses={
            200: "Login Success",
            400: "Validation Error",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Account Not Found",
            500: "Internal Server Error",
            503: "Service Unavailable",
        },
    )
    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "message": "Validation Error",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            account = Account.objects.get(
                email=serializer.validated_data["email"]
            )

            if not check_password(
                serializer.validated_data["password"],
                account.password,
            ):

                return Response(
                    {
                        "message": "Invalid Email or Password"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            return Response(
                {
                    "message": "Login Success",
                    "user_id": account.user_id,
                    "email": account.email,
                },
                status=status.HTTP_200_OK,
            )

        except Account.DoesNotExist:

            return Response(
                {
                    "message": "Account Not Found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception:

            return Response(
                {
                    "message": "Internal Server Error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterView(APIView):

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Register",
        operation_description="Register account",
        request_body=RegisterSerializer,
        responses={
            200: "Register Success",
            400: "Validation Error",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            503: "Service Unavailable",
        },
    )
    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "message": "Validation Error",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            account = Account.objects.create(
                email=serializer.validated_data["email"],
                password=make_password(
                    serializer.validated_data["password"]
                ),
            )

            verify = MailService.send_verify_email(
                account
            )

            return Response(
                {
                    "message": "Register Success",
                    "user_id": account.user_id,
                    "email": account.email,
                    "verify_id": verify.verify_id,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {
                    "message": "Internal Server Error",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SendVerifyCodeView(APIView):

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Send Verify Code",
        operation_description="Send a 6-digit verification code to the registered email.",
        request_body=SendVerifyCodeSerializer,
        responses={
            200: "Verification Code Sent",
            400: "Validation Error",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Account Not Found",
            500: "Internal Server Error",
            503: "Service Unavailable",
        },
    )
    def post(self, request):

        serializer = SendVerifyCodeSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "message": "Validation Error",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            account = serializer.account

            verify = MailService.send_verify_email(
                account
            )

            return Response(
                {
                    "message": "Verification code sent successfully.",
                    "data": {
                        "verify_id": verify.verify_id,
                        "user_id": account.user_id,
                        "email": account.email,
                        "verify_code": verify.verify_code,
                        "verify_status": verify.verify_status,
                        "create_time": verify.create_time,
                        "verify_time": verify.verify_time,
                        "lock_time": verify.lock_time,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {
                    "message": "Internal Server Error",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )