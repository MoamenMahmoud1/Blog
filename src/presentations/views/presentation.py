import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from presentations.models import Presentation
from presentations.selectors import get_presentation_with_cards
from presentations.serializers import serialize_presentation
from presentations.services import create_presentation


class PresentationListView(View):
    def get(self, request):
        presentations = (
            Presentation.objects.filter(status=Presentation.Status.PUBLISHED)
            .values(
                "id",
                "title",
                "created",
            )
            .order_by("-created")
        )

        return JsonResponse(
            {
                "presentations": list(presentations),
            }
        )


class PresentationDetailView(View):
    def get(self, request, presentation_id):
        try:
            presentation = get_presentation_with_cards(presentation_id=presentation_id)
        except Presentation.DoesNotExist:
            return JsonResponse(
                {"detail": "Presentation not found."},
                status=404,
            )

        return JsonResponse(serialize_presentation(presentation))


class PresentationCreateView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"detail": "Invalid JSON."},
                status=400,
            )

        title = data.get("title", "").strip()

        if not title:
            return JsonResponse(
                {"detail": "Title is required."},
                status=400,
            )

        presentation = create_presentation(
            author=request.user,
            title=title,
        )

        return JsonResponse(
            {
                "id": presentation.id,
                "title": presentation.title,
            },
            status=201,
        )
