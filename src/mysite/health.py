import secrets

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views import View


class LivenessView(View):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        response = JsonResponse({"status": "ok"})
        response.headers["Cache-Control"] = "no-store"
        return response


class ReadinessView(View):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        try:
            self._check_database()
            self._check_cache()
        except Exception:
            response = JsonResponse({"status": "unavailable"}, status=503)
        else:
            response = JsonResponse({"status": "ok"})

        response.headers["Cache-Control"] = "no-store"
        return response

    @staticmethod
    def _check_database():
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                raise RuntimeError("Database readiness check failed.")

    @staticmethod
    def _check_cache():
        key = f"healthcheck:{secrets.token_hex(8)}"
        value = secrets.token_urlsafe(16)

        cache.set(key, value, timeout=5)
        if cache.get(key) != value:
            raise RuntimeError("Cache readiness check failed.")

        cache.delete(key)
