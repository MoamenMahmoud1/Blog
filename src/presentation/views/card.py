from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from presentation.models import Card, Presentation
from presentation.services import (
    create_child_card,
    create_main_card,
)


class MainCardCreateView(LoginRequiredMixin, View):
    def post(self, request, presentation_id):
        presentation = Presentation.objects.filter(
            id=presentation_id,
            author=request.user,
        ).first()

        if presentation is None:
            return JsonResponse(
                {"detail": "Presentation not found."},
                status=404,
            )

        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "")

        if not title:
            return JsonResponse(
                {"detail": "Title is required."},
                status=400,
            )

        card = create_main_card(
            presentation=presentation,
            title=title,
            content=content,
            image=request.FILES.get("image"),
            video=request.FILES.get("video"),
        )

        return JsonResponse(
            {
                "id": card.id,
                "title": card.title,
                "order": card.order,
                "is_main": True,
            },
            status=201,
        )


class ChildCardCreateView(LoginRequiredMixin, View):
    def post(self, request, parent_id):
        parent = (
            Card.objects.select_related("presentation")
            .filter(
                id=parent_id,
                presentation__author=request.user,
            )
            .first()
        )

        if parent is None:
            return JsonResponse(
                {"detail": "Parent card not found."},
                status=404,
            )

        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "")

        if not title:
            return JsonResponse(
                {"detail": "Title is required."},
                status=400,
            )

        card = create_child_card(
            parent=parent,
            title=title,
            content=content,
            image=request.FILES.get("image"),
            video=request.FILES.get("video"),
        )

        return JsonResponse(
            {
                "id": card.id,
                "title": card.title,
                "order": card.order,
                "parent_id": card.parent_id,
                "is_main": False,
            },
            status=201,
        )
