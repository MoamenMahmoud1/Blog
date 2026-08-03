import markdown
import nh3
from django.utils.safestring import mark_safe

ALLOWED_TAGS = {
    "a",
    "blockquote",
    "br",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "ul",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "code": {"class"},
}


def render_markdown(text):
    """Render Markdown while removing unsafe HTML, URLs, and attributes."""

    rendered = markdown.markdown(
        text or "",
        extensions=["extra", "sane_lists"],
        output_format="html",
    )
    cleaned = nh3.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        clean_content_tags={"script", "style"},
        url_schemes={"http", "https", "mailto"},
        url_relative="deny",
    )
    return mark_safe(cleaned)  # noqa: S308 -- nh3 sanitized with a strict allowlist.
