"""No-count batching helpers for progressively loaded querysets."""

from django.core import signing
from django.db.models import Q
from django.utils.dateparse import parse_datetime

DEFAULT_MAX_PAGE = 1000
POST_CURSOR_SALT = "blog.post-feed"


def parse_page_number(value, *, max_page=DEFAULT_MAX_PAGE):
    try:
        page = int(value)
    except (TypeError, ValueError):
        page = 1
    return max(1, min(page, max_page))


def queryset_batch(queryset, *, page, page_size, max_page=DEFAULT_MAX_PAGE):
    """Fetch one extra row to detect another batch without a COUNT query."""

    offset = (page - 1) * page_size
    matches = list(queryset[offset : offset + page_size + 1])
    has_more = len(matches) > page_size and page < max_page
    return matches[:page_size], has_more


def _decode_post_cursor(cursor):
    if not cursor:
        return None
    try:
        publish_value, post_id = signing.loads(cursor, salt=POST_CURSOR_SALT)
        publish = parse_datetime(publish_value)
        post_id = int(post_id)
    except (signing.BadSignature, TypeError, ValueError):
        return None
    if publish is None or post_id < 1:
        return None
    return publish, post_id


def _encode_post_cursor(post):
    return signing.dumps(
        [post.publish.isoformat(), post.pk],
        salt=POST_CURSOR_SALT,
        compress=True,
    )


def post_cursor_batch(queryset, *, cursor, page_size):
    """Return a stable post batch using indexed keyset pagination."""

    cursor_values = _decode_post_cursor(cursor)
    if cursor_values:
        publish, post_id = cursor_values
        queryset = queryset.filter(
            Q(publish__lt=publish) | Q(publish=publish, pk__lt=post_id)
        )

    matches = list(queryset.order_by("-publish", "-pk")[: page_size + 1])
    posts = matches[:page_size]
    next_cursor = _encode_post_cursor(posts[-1]) if len(matches) > page_size else None
    return posts, next_cursor
