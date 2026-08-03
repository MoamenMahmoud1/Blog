from django import template
from django.db.models import Count, Q

from blog.markdown import render_markdown
from blog.models import Post

register = template.Library()


@register.simple_tag
def total_posts():
    return Post.published.count()


@register.inclusion_tag("post/latest_posts.html")
def show_latest_posts(count=5):
    latest_posts = Post.published.only("title", "slug", "publish")[:count]
    return {"latest_posts": latest_posts}


@register.simple_tag
def get_most_commented_posts(count=5):
    return (
        Post.published.annotate(
            total_comments=Count(
                "comments",
                filter=Q(comments__active=True),
            )
        )
        .only("title", "slug", "publish")
        .order_by("-total_comments", "-publish")[:count]
    )


@register.filter(name="markdown")
def markdown_format(text):
    return render_markdown(text)
