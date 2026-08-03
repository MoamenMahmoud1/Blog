import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views import View


class PublicProfileMediaView(View):
    http_method_names = ["get", "head", "options"]

    def get(self, request, path):
        media_root = (Path(settings.MEDIA_ROOT) / "profiles").resolve()
        file_path = (media_root / path).resolve()

        if not file_path.is_relative_to(media_root) or not file_path.is_file():
            raise Http404

        content_type = mimetypes.guess_type(file_path.name)[0]
        if not content_type or not content_type.startswith("image/"):
            raise Http404

        response = FileResponse(file_path.open("rb"), content_type=content_type)
        response.headers["Cache-Control"] = "public, max-age=86400"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
