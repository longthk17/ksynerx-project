from django.core.cache import cache
from django.db import connections
from rest_framework import status
from rest_framework.views import APIView

from my_app.apps import API_VERSION, SERVICE_NAME
from my_app.utils import response


class HealthCheckView(APIView):
    def get(self, request):
        # Check database connection
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1")
                db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Check cache connection
        try:
            cache.set("health_check", "ok", timeout=5)
            if cache.get("health_check") == "ok":
                cache_status = "healthy"
            else:
                cache_status = "unhealthy"
        except Exception:
            cache_status = "unhealthy"

        response_data = {
            "status": (
                "healthy"
                if db_status == "healthy" and cache_status == "healthy"
                else "unhealthy"
            ),
            "database": db_status,
            "cache": cache_status,
            "serviceName": SERVICE_NAME,
            "apiVersion": API_VERSION,
        }
        return response(
            data=response_data,
            message="Health check completed",
            status_code=status.HTTP_200_OK,
        )
