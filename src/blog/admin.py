from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Comment, Post, Profile
from .permissions import PUBLISH_POST_PERMISSION


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "author", "publish", "status", "id")
    list_filter = ("status", "created", "publish", "author")
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("author",)
    date_hierarchy = "publish"
    ordering = ("status", "publish")
    show_facets = admin.ShowFacets.ALLOW
    list_select_related = ("author",)
    list_per_page = 50

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(author=request.user)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        readonly_fields = ["author"]
        if not request.user.has_perm(PUBLISH_POST_PERMISSION):
            readonly_fields.extend(["status", "publish"])
        return tuple(readonly_fields)

    def has_change_permission(self, request, obj=None):
        allowed = super().has_change_permission(request, obj)
        if not allowed or obj is None or request.user.is_superuser:
            return allowed
        if obj.author_id != request.user.pk:
            return False
        return obj.status == Post.Status.DRAFT or request.user.has_perm(
            PUBLISH_POST_PERMISSION
        )

    def has_delete_permission(self, request, obj=None):
        allowed = super().has_delete_permission(request, obj)
        if not allowed or obj is None or request.user.is_superuser:
            return allowed
        return obj.author_id == request.user.pk

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.author = request.user
            if not request.user.has_perm(PUBLISH_POST_PERMISSION):
                obj.status = Post.Status.DRAFT
        super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "post_link", "created", "active")
    list_filter = ("active", "created", "updated")
    search_fields = ("name", "email", "body")
    list_select_related = ("post",)
    list_per_page = 50

    @admin.display(description="Post")
    def post_link(self, obj):
        url = reverse("admin:blog_post_change", args=[obj.post_id])
        return format_html('<a href="{}">{}</a>', url, obj.post.title)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "img")
