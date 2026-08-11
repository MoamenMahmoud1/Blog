import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from presentation.models import Presentation
from presentation.selectors import get_presentation_with_cards
from presentation.serializers import serialize_presentation
from presentation.services import create_presentation


class PresentationListView(View):
    def get(self, request):
        presentations = (
            Presentation.objects.filter(
                status=Presentation.Status.PUBLISHED,
            )
            .values(
                "id",
                "title",
                "created",
            )
            .order_by("-created")
        )

        return render(
            request,
            "presentation/presentation_list.html",
            {
                "presentations": presentations,
            },
        )


class PresentationDetailView(View):
    def get(self, request, presentation_id):
        try:
            presentation = get_presentation_with_cards(
                presentation_id=presentation_id,
            )
        except Presentation.DoesNotExist:
            return render(
                request,
                "404.html",
                status=404,
            )

        presentation_data = serialize_presentation(presentation)

        return render(
            request,
            "presentations/presentation_detail.html",
            {
                "presentation": presentation,
                "presentation_data": json.dumps(presentation_data),
            },
        )


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
