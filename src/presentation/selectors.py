from django.db.models import Prefetch

from .models import Card, Presentation


def get_presentation_with_cards(*, presentation_id: int) -> Presentation:
    main_cards = (
        Card.objects.filter(parent__isnull=True)
        .prefetch_related(
            Prefetch(
                "children",
                queryset=Card.objects.order_by("order", "id"),
            )
        )
        .order_by("order", "id")
    )

    return (
        Presentation.objects.filter(
            id=presentation_id,
            status=Presentation.Status.PUBLISHED,
        )
        .prefetch_related(
            Prefetch(
                "cards",
                queryset=main_cards,
                to_attr="main_cards",
            )
        )
        .get()
    )
