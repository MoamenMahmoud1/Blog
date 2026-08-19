from django.urls import path

from .feeds import LatestPostsFeed
from .views import accounts, dashboard, public, search

app_name = "blog"

urlpatterns = [
    path("", public.PostListView.as_view(), name="post_list"),
    path(
        "tag/<slug:tag_slug>/",
        public.PostListView.as_view(),
        name="post_list_by_tag",
    ),
    path("<int:pk>/edit/", accounts.ProfileUpdateView.as_view(), name="edit-profile"),
    path(
        "<int:year>/<int:month>/<int:day>/<str:post>/",
        public.PostDetailView.as_view(),
        name="post_detail",
    ),
    path("<int:post_id>/share/", public.PostShareView.as_view(), name="post_share"),
    path(
        "<int:post_id>/comment/",
        public.PostCommentView.as_view(),
        name="post_comment",
    ),
    path("feed/", LatestPostsFeed(), name="post_feed"),
    path(
        "search/suggestions/",
        search.PostSearchSuggestionsView.as_view(),
        name="post_search_suggestions",
    ),
    path("search/", search.PostSearchView.as_view(), name="post_search"),
    path("signup/", accounts.SignUpView.as_view(), name="signup"),
    path("login/", accounts.LoginView.as_view(), name="login"),
    path("logout/", accounts.LogoutView.as_view(), name="logout"),
    path("dashboard/", dashboard.AuthorDashboardView.as_view(), name="dashboard"),
    path(
        "dashboard/posts/create/",
        dashboard.CreatePostView.as_view(),
        name="create_post",
    ),
    path(
        "dashboard/posts/<int:pk>/edit/",
        dashboard.UpdatePostView.as_view(),
        name="post_update",
    ),
    path(
        "dashboard/posts/<int:pk>/delete/",
        dashboard.DeletePostView.as_view(),
        name="post_delete",
    ),
    path(
        "dashboard/posts/<int:pk>/publish/",
        dashboard.PublishPostView.as_view(),
        name="post_publish",
    ),
    path(
        "dashboard/posts/<int:pk>/unpublish/",
        dashboard.UnpublishPostView.as_view(),
        name="post_unpublish",
    ),
]
