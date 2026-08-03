from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Count, Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic import DetailView, FormView, ListView
from taggit.models import Tag

from ..forms import CommentForm, EmailPostForm
from ..models import Comment, Post
from ..pagination import post_cursor_batch
from ..selectors import published_posts


class PublishedPostMixin:
    model = Post

    def get_queryset(self):
        return published_posts()


class PostListView(PublishedPostMixin, ListView):
    context_object_name = "posts"
    template_name = "post/list.html"
    page_size = 6

    def get_template_names(self):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return ["post/includes/post_list_items.html"]
        return [self.template_name]

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .only(
                "id",
                "title",
                "slug",
                "body",
                "publish",
                "author_id",
                "author__username",
            )
            .prefetch_related("tags")
        )
        self.tag = None
        self.next_cursor = None
        tag_slug = self.kwargs.get("tag_slug")
        if tag_slug:
            self.tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags=self.tag)

        posts, self.next_cursor = post_cursor_batch(
            queryset,
            cursor=self.request.GET.get("cursor"),
            page_size=self.page_size,
        )
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        context["next_cursor"] = self.next_cursor
        return context


class PostDetailView(PublishedPostMixin, DetailView):
    context_object_name = "post"
    template_name = "post/detail.html"
    slug_url_kwarg = "post"

    def get_queryset(self):
        active_comments = Comment.objects.filter(active=True).only(
            "post_id", "name", "body", "created"
        )
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "tags",
                Prefetch(
                    "comments",
                    queryset=active_comments,
                    to_attr="active_comments",
                ),
            )
        )

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        return get_object_or_404(
            queryset,
            slug=self.kwargs["post"],
            publish__year=self.kwargs["year"],
            publish__month=self.kwargs["month"],
            publish__day=self.kwargs["day"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_ids = [tag.pk for tag in self.object.tags.all()]
        similar_posts = Post.published.select_related("author").filter(tags__in=tag_ids)
        similar_posts = (
            similar_posts.exclude(pk=self.object.pk)
            .annotate(same_tags=Count("tags", distinct=True))
            .order_by("-same_tags", "-publish")[:4]
        )
        context.update(
            {
                "comments": self.object.active_comments,
                "form": getattr(self.request, "_comment_form", CommentForm()),
                "similar_posts": similar_posts,
            }
        )
        return context


class PostShareView(LoginRequiredMixin, PublishedPostMixin, FormView):
    form_class = EmailPostForm
    template_name = "post/share.html"
    raise_exception = False

    @cached_property
    def post_object(self):
        return get_object_or_404(
            self.get_queryset(),
            pk=self.kwargs["post_id"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post"] = self.post_object
        context.setdefault("sent", False)
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        recipient_email = data["to"].strip()

        User = get_user_model()

        if not User.objects.filter(
            email__iexact=recipient_email,
        ).exists():
            form.add_error(
                "to",
                "This email does not belong to a registered user.",
            )
            return self.form_invalid(form)

        throttle_key = f"post-share:{self.request.user.pk}"

        if not cache.add(throttle_key, True, timeout=60):
            form.add_error(
                None,
                "Please wait before sending another email.",
            )
            return self.form_invalid(form)

        post_url = self.request.build_absolute_uri(self.post_object.get_absolute_url())
        safe_title = " ".join(self.post_object.title.splitlines())

        subject = f"{data['name']} ({data['email']}) recommends you read {safe_title}"

        message = (
            f"Read {self.post_object.title} at {post_url}\n\n"
            f"{data['name']}'s comments: {data['comments']}"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
        except Exception:
            cache.delete(throttle_key)
            form.add_error(
                None,
                "Email delivery is temporarily unavailable. Please try again.",
            )
            return self.form_invalid(form)

        return self.render_to_response(
            self.get_context_data(
                form=form,
                sent=True,
            )
        )


class PostCommentView(FormView):
    form_class = CommentForm
    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        self.post_object = get_object_or_404(Post.published, pk=kwargs["post_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        client_address = self.request.META.get("REMOTE_ADDR", "unknown")
        throttle_key = f"post-comment:{self.post_object.pk}:{client_address}"
        if not cache.add(throttle_key, True, timeout=30):
            form.add_error(None, "Please wait before adding another comment.")
            return self.form_invalid(form)

        comment = form.save(commit=False)
        comment.post = self.post_object
        comment.save()
        return HttpResponseRedirect(f"{self.post_object.get_absolute_url()}#comments")

    def form_invalid(self, form):
        detail_view = PostDetailView()
        detail_view.setup(self.request, **self._detail_kwargs(form))
        detail_view.object = detail_view.get_object()
        context = detail_view.get_context_data(object=detail_view.object)
        return detail_view.render_to_response(context, status=400)

    def _detail_kwargs(self, form):
        publish = self.post_object.publish
        self.request._comment_form = form
        return {
            "year": publish.year,
            "month": publish.month,
            "day": publish.day,
            "post": self.post_object.slug,
        }
