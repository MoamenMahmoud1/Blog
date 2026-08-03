from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

AUTHOR_GROUP_NAME = "Blog authors"
AUTHOR_PERMISSION_CODENAMES = (
    "view_post",
    "add_post",
    "change_post",
    "delete_post",
)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def initialize_user_account(sender, instance, created, raw=False, **kwargs):
    if not created or raw:
        return

    Profile.objects.get_or_create(user=instance)
    if instance.is_superuser:
        return

    author_group, _ = Group.objects.get_or_create(name=AUTHOR_GROUP_NAME)
    author_permissions = Permission.objects.filter(
        content_type__app_label="blog",
        content_type__model="post",
        codename__in=AUTHOR_PERMISSION_CODENAMES,
    )
    author_group.permissions.add(*author_permissions)
    instance.groups.add(author_group)
