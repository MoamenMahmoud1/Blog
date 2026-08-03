from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from ..forms import PostForm
from ..markdown import render_markdown
from ..models import Post
from ..permissions import (
    ADD_POST_PERMISSION,
    CHANGE_POST_PERMISSION,
    DELETE_POST_PERMISSION,
    PUBLISH_POST_PERMISSION,
    AuthenticatedPermissionMixin,
    AuthorPostQuerysetMixin,
    EditablePostQuerysetMixin,
    PublishCapabilityMixin,
)
from ..selectors import manageable_posts_for
from ..services import (
    prepare_post_as_draft,
    prepare_post_for_publication,
    update_post_publication,
)


class AuthorDashboardView(LoginRequiredMixin, ListView):
    context_object_name = "posts"
    template_name = "blog/dashboard.html"
    paginate_by = 10

    def get_queryset(self):
        queryset = manageable_posts_for(self.request.user).prefetch_related("tags")
        status = self.request.GET.get("status")
        if status == "draft":
            queryset = queryset.filter(status=Post.Status.DRAFT)
        elif status == "published":
            queryset = queryset.filter(
                status=Post.Status.PUBLISHED,
                publish__lte=timezone.now(),
            )
        elif status == "scheduled":
            queryset = queryset.filter(
                status=Post.Status.PUBLISHED,
                publish__gt=timezone.now(),
            )
        self.status_filter = (
            status if status in {"draft", "published", "scheduled"} else "all"
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.status_filter
        return context


class PostFormActionMixin(PublishCapabilityMixin):
    form_class = PostForm
    template_name = "blog/post_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["can_publish"] = self.can_publish
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = bool(getattr(self, "object", None))
        context["can_publish"] = self.can_publish
        return context

    def form_valid(self, form):
        action = self.request.POST.get("action", "save_draft")
        if action == "preview":
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    preview_html=render_markdown(form.cleaned_data["body"]),
                    preview_title=form.cleaned_data["title"],
                )
            )

        if action == "publish":
            if not self.can_publish:
                raise PermissionDenied
            prepare_post_for_publication(form.instance)
        else:
            prepare_post_as_draft(form.instance)

        response = super().form_valid(form)
        self._add_status_message(form.instance)
        return response

    def _add_status_message(self, post):
        if post.status == Post.Status.DRAFT:
            message = "Post saved as a draft."
        elif post.publish > timezone.now():
            message = "Post scheduled successfully."
        else:
            message = "Post published successfully."
        messages.success(self.request, message)

    def get_success_url(self):
        return reverse("blog:dashboard")


class CreatePostView(
    AuthenticatedPermissionMixin,
    PostFormActionMixin,
    CreateView,
):
    model = Post
    permission_required = ADD_POST_PERMISSION

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class UpdatePostView(
    AuthenticatedPermissionMixin,
    EditablePostQuerysetMixin,
    PostFormActionMixin,
    UpdateView,
):
    permission_required = CHANGE_POST_PERMISSION


class DeletePostView(
    AuthenticatedPermissionMixin,
    AuthorPostQuerysetMixin,
    DeleteView,
):
    permission_required = DELETE_POST_PERMISSION
    context_object_name = "post"
    template_name = "blog/post_confirm_delete.html"
    success_url = reverse_lazy("blog:dashboard")

    def form_valid(self, form):
        messages.success(self.request, "Post deleted successfully.")
        return super().form_valid(form)


class PostPublicationView(
    AuthenticatedPermissionMixin,
    AuthorPostQuerysetMixin,
    View,
):
    permission_required = (CHANGE_POST_PERMISSION, PUBLISH_POST_PERMISSION)
    http_method_names = ["post"]
    target_status = None

    def post(self, request, *args, **kwargs):
        post = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        update_post_publication(post, self.target_status)
        if post.status == Post.Status.DRAFT:
            message = "Post moved back to drafts."
        elif post.publish > timezone.now():
            message = "Post scheduled successfully."
        else:
            message = "Post published successfully."
        messages.success(request, message)
        return HttpResponseRedirect(reverse("blog:dashboard"))


class PublishPostView(PostPublicationView):
    target_status = Post.Status.PUBLISHED


class UnpublishPostView(PostPublicationView):
    target_status = Post.Status.DRAFT
