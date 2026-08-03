"""Small write-side operations for post publication state."""

from django.utils import timezone

from .models import Post


def prepare_post_for_publication(post):
    post.status = Post.Status.PUBLISHED
    now = timezone.now()
    post.publish = max(now, post.publish)
    return post


def prepare_post_as_draft(post):
    post.status = Post.Status.DRAFT
    return post


def update_post_publication(post, status):
    if status == Post.Status.PUBLISHED:
        original_publish = post.publish
        prepare_post_for_publication(post)
        update_fields = ["status", "updated"]
        if post.publish != original_publish:
            update_fields.append("publish")
    else:
        prepare_post_as_draft(post)
        update_fields = ["status", "updated"]

    post.save(update_fields=update_fields)
    return post
