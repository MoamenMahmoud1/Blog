from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Presentation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="presentations",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title


class Card(models.Model):
    presentation = models.ForeignKey(
        Presentation,
        on_delete=models.CASCADE,
        related_name="cards",
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)

    order = models.PositiveIntegerField()

    image = models.ImageField(
        upload_to="presentations/images/%Y/%m/%d/",
        blank=True,
    )

    video = models.FileField(
        upload_to="presentations/videos/%Y/%m/%d/",
        blank=True,
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

        constraints = [
            models.CheckConstraint(
                condition=~Q(id=F("parent_id")),
                name="card_cannot_parent_itself",
            ),
            models.UniqueConstraint(
                fields=["presentation", "order"],
                condition=Q(parent__isnull=True),
                name="unique_main_card_order",
            ),
            models.UniqueConstraint(
                fields=["parent", "order"],
                condition=Q(parent__isnull=False),
                name="unique_child_card_order",
            ),
        ]

        indexes = [
            models.Index(
                fields=["presentation", "parent", "order"],
                name="card_tree_order_idx",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def is_main(self):
        return self.parent_id is None

    def clean(self):
        super().clean()

        if self.parent_id is None:
            return

        if self.parent_id == self.pk:
            raise ValidationError({"parent": "A card cannot be its own parent."})

        if self.parent.presentation_id != self.presentation_id:
            raise ValidationError(
                {"parent": ("Parent must belong to the same presentation.")}
            )

        if self.parent.parent_id is not None:
            raise ValidationError({"parent": "Child cards cannot have children."})
