from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from .models import Card, Presentation


def get_next_main_order(*, presentation: Presentation) -> int:
    max_order = Card.objects.filter(
        presentation=presentation,
        parent__isnull=True,
    ).aggregate(max_order=Max("order"))["max_order"]

    return (max_order or 0) + 1


def get_next_child_order(*, parent: Card) -> int:
    max_order = parent.children.aggregate(max_order=Max("order"))["max_order"]

    return (max_order or 0) + 1


@transaction.atomic
def create_presentation(
    *,
    author,
    title: str,
) -> Presentation:
    presentation = Presentation(
        author=author,
        title=title,
    )

    presentation.full_clean()
    presentation.save()

    return presentation


@transaction.atomic
def create_main_card(
    *,
    presentation: Presentation,
    title: str,
    content: str = "",
    image=None,
    video=None,
) -> Card:
    card = Card(
        presentation=presentation,
        parent=None,
        title=title,
        content=content,
        order=get_next_main_order(presentation=presentation),
        image=image,
        video=video,
    )

    card.full_clean()
    card.save()

    return card


@transaction.atomic
def create_child_card(
    *,
    parent: Card,
    title: str,
    content: str = "",
    image=None,
    video=None,
) -> Card:
    if not parent.is_main:
        raise ValidationError("Child cards can only belong to a main card.")

    card = Card(
        presentation=parent.presentation,
        parent=parent,
        title=title,
        content=content,
        order=get_next_child_order(parent=parent),
        image=image,
        video=video,
    )

    card.full_clean()
    card.save()

    return card
