from django.urls import path

from presentations.views.card import (
    ChildCardCreateView,
    MainCardCreateView,
)
from presentations.views.presentation import (
    PresentationCreateView,
    PresentationDetailView,
    PresentationListView,
)

app_name = "presentations"


urlpatterns = [
    path(
        "",
        PresentationListView.as_view(),
        name="list",
    ),
    path(
        "create/",
        PresentationCreateView.as_view(),
        name="create",
    ),
    path(
        "<int:presentation_id>/",
        PresentationDetailView.as_view(),
        name="detail",
    ),
    path(
        "<int:presentation_id>/cards/",
        MainCardCreateView.as_view(),
        name="main-card-create",
    ),
    path(
        "cards/<int:parent_id>/children/",
        ChildCardCreateView.as_view(),
        name="child-card-create",
    ),
]
