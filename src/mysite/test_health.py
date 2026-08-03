from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse


class HealthEndpointTests(TestCase):
    def test_liveness_endpoint_returns_ok_without_caching(self):
        response = self.client.get(reverse("health-live"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_readiness_endpoint_checks_dependencies(self):
        response = self.client.get(reverse("health-ready"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    @patch(
        "mysite.health.connection.cursor",
        side_effect=DatabaseError("database unavailable"),
    )
    def test_readiness_returns_503_when_database_is_unavailable(self, mocked_cursor):
        response = self.client.get(reverse("health-ready"))

        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(response.content, {"status": "unavailable"})

    @patch(
        "mysite.health.cache.set",
        side_effect=ConnectionError("cache unavailable"),
    )
    def test_readiness_returns_503_when_cache_is_unavailable(self, mocked_cache):
        response = self.client.get(reverse("health-ready"))

        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(response.content, {"status": "unavailable"})

    def test_health_endpoints_support_head_requests(self):
        self.assertEqual(self.client.head(reverse("health-live")).status_code, 200)
        self.assertEqual(self.client.head(reverse("health-ready")).status_code, 200)

    def test_health_endpoints_reject_post_requests(self):
        self.assertEqual(self.client.post(reverse("health-live")).status_code, 405)
        self.assertEqual(self.client.post(reverse("health-ready")).status_code, 405)
