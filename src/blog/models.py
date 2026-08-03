from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from taggit.managers import TaggableManager


class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                status=Post.Status.PUBLISHED,
                publish__lte=timezone.now(),
            )
        )


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DF", "Draft"
        PUBLISHED = "PB", "Published"

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    body = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2,
        choices=Status,
        default=Status.DRAFT,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_posts",
    )
    tags = TaggableManager()

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-publish"]
        permissions = [
            ("publish_post", "Can publish and schedule posts"),
        ]
        indexes = [
            models.Index(fields=["-publish"], name="post_publish_idx"),
            models.Index(
                fields=["status", "-publish", "-id"],
                name="post_status_publish_idx",
            ),
            GinIndex(
                SearchVector("title", weight="A", config="simple")
                + SearchVector("body", weight="B", config="simple"),
                name="post_search_gin_idx",
            ),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True) or "post"
            slug = base_slug[:250]
            suffix = 2
            matching_posts = Post.objects.filter(slug=slug)
            if self.pk:
                matching_posts = matching_posts.exclude(pk=self.pk)
            while matching_posts.exists():
                suffix_text = f"-{suffix}"
                slug = f"{base_slug[: 250 - len(suffix_text)]}{suffix_text}"
                matching_posts = Post.objects.filter(slug=slug)
                if self.pk:
                    matching_posts = matching_posts.exclude(pk=self.pk)
                suffix += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "blog:post_detail",
            args=[
                self.publish.year,
                self.publish.month,
                self.publish.day,
                self.slug,
            ],
        )

    @property
    def publication_state(self):
        if self.status == self.Status.DRAFT:
            return "Draft"
        if self.publish > timezone.now():
            return "Scheduled"
        return "Published"


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["created"]
        indexes = [
            models.Index(fields=["created"], name="comment_created_idx"),
            models.Index(
                fields=["post", "active", "created"],
                name="comment_post_active_idx",
            ),
        ]

    def __str__(self):
        return f"Comment by {self.name} on {self.post}"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    img = models.ImageField(
        upload_to="profiles/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Profile for {self.user.get_username()}"
