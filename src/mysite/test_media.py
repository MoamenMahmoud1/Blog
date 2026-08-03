from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.urls import reverse


class PublicProfileMediaTests(TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.media_root = Path(self.temporary_directory.name)

    def test_profile_image_is_served_with_safe_cache_headers(self):
        profile_directory = self.media_root / "profiles"
        profile_directory.mkdir()
        (profile_directory / "avatar.png").write_bytes(b"profile-image")

        with override_settings(DEBUG=False, MEDIA_ROOT=self.media_root):
            response = self.client.get(
                reverse("public-profile-media", kwargs={"path": "avatar.png"})
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "image/png")
        self.assertEqual(response.headers["Cache-Control"], "public, max-age=86400")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")

    def test_missing_profile_image_returns_not_found(self):
        with override_settings(DEBUG=False, MEDIA_ROOT=self.media_root):
            response = self.client.get(
                reverse("public-profile-media", kwargs={"path": "missing.png"})
            )

        self.assertEqual(response.status_code, 404)
