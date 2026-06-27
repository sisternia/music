from django.contrib.auth.hashers import check_password, make_password

from drf_yasg.utils import swagger_auto_schema

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account
from .models import VerifyAccount
from apps.roles_permissions.models import RoleAccount
from .serializers import (
    LoginSerializer,
    LoginResponseSerializer,
    RegisterSerializer,
    RegisterResponseSerializer,
    ResetPasswordRequestSerializer,
    ResetPasswordResponseSerializer,
    SendVerifyCodeSerializer,
    SendVerifyCodeResponseSerializer,
    VerifyCodeSerializer,
    VerifyCodeCheckResponseSerializer,
    VerifyCodeConfirmResponseSerializer,
)
from .admin_serializers import (
    UserDisplayResponseSerializer,
)
from .services import MailService
from .services import VerifyCodeService


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

            verify = (
                VerifyAccount.objects.filter(
                    user=account,
                )
                .order_by("-create_time")
                .first()
            )

            if not verify or verify.verify_status == VerifyAccount.VerifyStatus.UNVERIFIED:

                return Response(
                    {
                        "message": "Account is not verified."
                    },
                    status=status.HTTP_403_FORBIDDEN,
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
                LoginResponseSerializer(
                    {
                        "message": "Login Success",
                        "user_id": account.user_id,
                        "email": account.email,
                    }
                ).data,
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
                role=RoleAccount.objects.get(
                    role_code=RoleAccount.RoleCode.USER
                ),
            )

            verify = MailService.send_verify_email(
                account
            )

            return Response(
                RegisterResponseSerializer(
                    {
                        "message": "Register Success",
                        "user_id": account.user_id,
                        "email": account.email,
                        "verify_id": verify.verify_id,
                    }
                ).data,
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
                SendVerifyCodeResponseSerializer(
                    {
                        "message": "Verification code sent successfully.",
                        "verify_id": verify.verify_id,
                        "user_id": account.user_id,
                        "email": account.email,
                        "verify_code": verify.verify_code,
                        "verify_status": verify.verify_status,
                        "create_time": verify.create_time,
                        "verify_time": verify.verify_time,
                        "lock_time": verify.lock_time,
                        "expire_at": VerifyCodeService.get_expire_at(verify),
                        "expire_minutes": VerifyCodeService.get_expire_minutes(),
                    }
                ).data,
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


class CheckVerifyCodeView(APIView):

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Check Verify Code Expiry",
        operation_description="Check whether a 6-digit verification code is still valid or expired.",
        request_body=VerifyCodeSerializer,
        responses={
            200: VerifyCodeCheckResponseSerializer,
            400: "Validation Error",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            503: "Service Unavailable",
        },
    )
    def post(self, request):

        serializer = VerifyCodeSerializer(
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

            result = VerifyCodeService.check_code(
                email=serializer.validated_data["email"],
                verify_code=serializer.validated_data["verify_code"],
            )

        except Exception as e:

            return Response(
                {
                    "message": "Service Unavailable",
                    "error": str(e),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not result["exists"]:

            return Response(
                {
                    "message": result["message"],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            VerifyCodeCheckResponseSerializer(
                {
                    "message": result["message"],
                    "verify_status": result["verify_status"],
                    "is_valid": result["is_valid"],
                    "is_expired": result["is_expired"],
                    "created_at": result["created_at"],
                    "expire_at": result["expire_at"],
                    "expire_minutes": VerifyCodeService.get_expire_minutes(),
                }
            ).data,
            status=status.HTTP_200_OK,
        )


class ConfirmVerifyCodeView(APIView):

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Confirm Verify Code",
        operation_description="Confirm the 6-digit verification code and mark the account as VERIFIED when it is correct and not expired.",
        request_body=VerifyCodeSerializer,
        responses={
            200: VerifyCodeConfirmResponseSerializer,
            400: "Validation Error",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            503: "Service Unavailable",
        },
    )
    def post(self, request):

        serializer = VerifyCodeSerializer(
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

            result = VerifyCodeService.confirm_code(
                email=serializer.validated_data["email"],
                verify_code=serializer.validated_data["verify_code"],
            )

        except Exception as e:

            return Response(
                {
                    "message": "Service Unavailable",
                    "error": str(e),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not result["exists"]:

            return Response(
                {
                    "message": result["message"],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not result.get("confirmed", False):

            return Response(
                {
                    "message": result["message"],
                    "data": {
                        "is_expired": result.get("is_expired", False),
                        "verify_status": result.get("verify_status"),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            VerifyCodeConfirmResponseSerializer(
                {
                    "message": result["message"],
                    "verify_status": result["verify_status"],
                    "verify_time": result.get("verify_time"),
                }
            ).data,
            status=status.HTTP_200_OK,
        )


class ValidateVerifyCodeView(APIView):

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Validate Verify Code",
        operation_description="Validate the 6-digit verification code without changing verify_status.",
        request_body=VerifyCodeSerializer,
        responses={
            200: VerifyCodeCheckResponseSerializer,
            400: "Validation Error",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            503: "Service Unavailable",
        },
    )
    def post(self, request):

        serializer = VerifyCodeSerializer(
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

            result = VerifyCodeService.validate_code(
                email=serializer.validated_data["email"],
                verify_code=serializer.validated_data["verify_code"],
            )

        except Exception as e:

            return Response(
                {
                    "message": "Service Unavailable",
                    "error": str(e),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not result["exists"]:

            return Response(
                {
                    "message": result["message"],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            VerifyCodeCheckResponseSerializer(
                {
                    "message": result["message"],
                    "verify_status": result["verify_status"],
                    "is_valid": result["is_valid"],
                    "is_expired": result["is_expired"],
                    "created_at": result["created_at"],
                    "expire_at": result["expire_at"],
                    "expire_minutes": VerifyCodeService.get_expire_minutes(),
                }
            ).data,
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Reset Password",
        operation_description="Set a new password without needing the old password.",
        request_body=ResetPasswordRequestSerializer,
        responses={
            200: "Reset Password Success",
            400: "Validation Error",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            503: "Service Unavailable",
        },
    )
    def post(self, request):

        serializer = ResetPasswordRequestSerializer(
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

            result = VerifyCodeService.reset_password(
                email=serializer.validated_data["email"],
                verify_code=serializer.validated_data["verify_code"],
                new_password=serializer.validated_data["new_password"],
            )

        except Exception as e:

            return Response(
                {
                    "message": "Service Unavailable",
                    "error": str(e),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not result["exists"]:

            return Response(
                {
                    "message": result["message"],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not result.get("reset", False):

            return Response(
                {
                    "message": result["message"],
                    "data": {
                        "is_expired": result.get("is_expired", False),
                        "verify_status": result.get("verify_status"),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ResetPasswordResponseSerializer(
                {
                    "message": result["message"],
                    "email": result["email"],
                    "user_id": result["user_id"],
                }
            ).data,
            status=status.HTTP_200_OK,
        )


class AdminUserListView(APIView):

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        tags=["Admin"],
        operation_summary="List Users",
        operation_description="Display user data.",
        responses={
            200: UserDisplayResponseSerializer,
            500: "Internal Server Error",
        },
    )
    def get(self, request):

        try:

            accounts = (
                Account.objects
                .select_related("role")
                .order_by("user_id")
            )

            data = [
                {
                    "user_id": account.user_id,
                    "email": account.email,
                    "role_id": account.role.role_id if account.role else None,
                    "role_code": account.role.role_code if account.role else None,
                    "role_name": account.role.role_name if account.role else None,
                    "create_time": account.create_time,
                    "update_time": account.update_time,
                }
                for account in accounts
            ]

            return Response(
                UserDisplayResponseSerializer(
                    {
                        "message": "User data retrieved successfully.",
                        "data": data,
                    }
                ).data,
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
