"""Permission names and object-level access rules used by blog views."""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import Post
from .selectors import manageable_posts_for

ADD_POST_PERMISSION = "blog.add_post"
CHANGE_POST_PERMISSION = "blog.change_post"
DELETE_POST_PERMISSION = "blog.delete_post"
PUBLISH_POST_PERMISSION = "blog.publish_post"


def can_publish_posts(user):
    return user.has_perm(PUBLISH_POST_PERMISSION)


class AuthenticatedPermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Redirect anonymous users and return 403 for authenticated users."""

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class PublishCapabilityMixin:
    @property
    def can_publish(self):
        return can_publish_posts(self.request.user)


class AuthorPostQuerysetMixin:
    model = Post

    def get_queryset(self):
        return manageable_posts_for(self.request.user)


class EditablePostQuerysetMixin(AuthorPostQuerysetMixin):
    """Authors edit drafts; publishers may also edit published posts."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if not can_publish_posts(self.request.user):
            queryset = queryset.filter(status=Post.Status.DRAFT)
        return queryset
