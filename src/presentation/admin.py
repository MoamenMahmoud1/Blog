from django.contrib import admin

from .models import Card, Presentation


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "status",
        "created",
        "updated",
    )

    list_filter = (
        "status",
        "created",
    )

    search_fields = (
        "title",
        "author__username",
    )


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "presentation",
        "parent",
        "order",
    )

    list_filter = ("presentation",)

    search_fields = (
        "title",
        "presentation__title",
    )
