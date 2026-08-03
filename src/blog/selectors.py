"""Reusable, read-only database queries for the blog application."""

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

from .models import Post
from .pagination import queryset_batch

SEARCH_CONFIG = "simple"


def published_posts():
    return Post.published.select_related("author")


def manageable_posts_for(user):
    queryset = Post.objects.select_related("author")
    if user.is_superuser:
        return queryset
    return queryset.filter(author=user)


def search_posts(query):
    search_vector = SearchVector(
        "title", weight="A", config=SEARCH_CONFIG
    ) + SearchVector("body", weight="B", config=SEARCH_CONFIG)
    search_query = SearchQuery(
        query,
        config=SEARCH_CONFIG,
        search_type="websearch",
    )
    return (
        published_posts()
        .only(
            "id",
            "title",
            "slug",
            "body",
            "publish",
            "author_id",
            "author__username",
        )
        .annotate(search_vector=search_vector)
        .filter(search_vector=search_query)
        .annotate(
            rank=SearchRank(
                search_vector,
                search_query,
                cover_density=True,
            )
        )
        .order_by("-rank", "-publish", "-pk")
    )


def search_batch(query, *, page, page_size, max_page=1000):
    """Return one page plus a flag without issuing a separate COUNT query."""

    return queryset_batch(
        search_posts(query),
        page=page,
        page_size=page_size,
        max_page=max_page,
    )
