from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework import permissions

from drf_yasg import openapi
from drf_yasg.views import get_schema_view


schema_view = get_schema_view(
    openapi.Info(
        title="Music Backend API",
        default_version="v1",
        description="API Documentation",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


def home(request):
    return JsonResponse(
        {
            "message": "Music Backend API",
            "version": "v1",
            "docs": {
                "swagger": "/swagger/",
                "redoc": "/redoc/",
            },
        }
    )


urlpatterns = [
    path("", home),

    path("admin/", admin.site.urls),

    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),

    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),

    path(
        "api/accounts/",
        include("apps.accounts.urls"),
    ),
]