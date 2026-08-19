from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from kombu.exceptions import OperationalError

from ..markdown import render_markdown
from ..models import Comment, Post


class BlogTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(
            username="author",
            email="author@example.com",
            password="test-password",
        )
        cls.author.groups.clear()
        cls.post = Post.objects.create(
            title="Published post",
            body="A **safe** post",
            author=cls.author,
            status=Post.Status.PUBLISHED,
            publish=timezone.now() - timedelta(hours=1),
        )
        cls.draft = Post.objects.create(
            title="Draft post",
            body="Not public",
            author=cls.author,
            status=Post.Status.DRAFT,
        )
        cls.future = Post.objects.create(
            title="Scheduled post",
            body="Not public yet",
            author=cls.author,
            status=Post.Status.PUBLISHED,
            publish=timezone.now() + timedelta(days=1),
        )

    def setUp(self):
        cache.clear()

    def login_with_permissions(self, user, *codenames):
        permissions = Permission.objects.filter(codename__in=codenames)
        user.user_permissions.add(*permissions)
        user = get_user_model().objects.get(pk=user.pk)
        self.client.force_login(user)
        return user

    def post_payload(self, **overrides):
        payload = {
            "title": "New post",
            "body": "Draft content",
            "tags": "django",
            "publish": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            "action": "save_draft",
        }
        payload.update(overrides)
        return payload


class PublicContentTests(BlogTestBase):
    def test_public_manager_hides_drafts_and_scheduled_posts(self):
        self.assertQuerySetEqual(Post.published.all(), [self.post])

    def test_list_and_detail_only_expose_published_posts(self):
        list_response = self.client.get(reverse("blog:post_list"))
        self.assertContains(list_response, self.post.title)
        self.assertContains(list_response, "blog/css/pages/post-list.css")
        self.assertContains(list_response, "blog/js/infinite-scroll.js")
        self.assertNotContains(list_response, self.draft.title)
        self.assertNotContains(list_response, self.future.title)
        self.assertIn("Content-Security-Policy", list_response.headers)
        self.assertIn(
            "script-src 'self' https://cdn.jsdelivr.net",
            list_response.headers["Content-Security-Policy"],
        )

        detail_response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(detail_response.status_code, 200)
        self.assertNotContains(detail_response, "blog/css/pages/post-list.css")
        self.assertNotContains(detail_response, "blog/css/pages/search.css")
        self.assertNotContains(detail_response, "blog/js/infinite-scroll.js")
        self.assertEqual(
            self.client.get(self.draft.get_absolute_url()).status_code, 404
        )
        self.assertEqual(
            self.client.get(self.future.get_absolute_url()).status_code, 404
        )

    def test_detail_url_accepts_unicode_slug(self):
        post = Post.objects.create(
            title="السلام عليكم",
            body="Arabic post",
            author=self.author,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )

        self.assertEqual(post.slug, "السلام-عليكم")
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)

    def test_post_feed_loads_database_batches_without_full_page_html(self):
        for number in range(7):
            Post.objects.create(
                title=f"Feed post {number}",
                body="Feed content",
                author=self.author,
                status=Post.Status.PUBLISHED,
                publish=timezone.now() - timedelta(minutes=number + 2),
            )

        with self.assertNumQueries(2):
            first_page = self.client.get(
                reverse("blog:post_list"),
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(len(first_page.context["posts"]), 6)
        next_cursor = first_page.context["next_cursor"]
        self.assertIsNotNone(next_cursor)
        self.assertNotContains(first_page, "<html")
        self.assertContains(first_page, "Load more posts")

        first_page_ids = {post.pk for post in first_page.context["posts"]}
        Post.objects.create(
            title="Published while scrolling",
            body="Newer than the cursor",
            author=self.author,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )
        with self.assertNumQueries(2):
            second_page = self.client.get(
                reverse("blog:post_list"),
                {"cursor": next_cursor},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        second_page_ids = {post.pk for post in second_page.context["posts"]}
        self.assertEqual(len(second_page_ids), 2)
        self.assertTrue(first_page_ids.isdisjoint(second_page_ids))
        self.assertIsNone(second_page.context["next_cursor"])
        self.assertNotContains(second_page, "Load more posts")

    def test_invalid_post_cursor_safely_returns_the_first_batch(self):
        response = self.client.get(
            reverse("blog:post_list"),
            {"cursor": "tampered"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["posts"][0], self.post)

    def test_comments_only_show_when_active(self):
        Comment.objects.create(
            post=self.post,
            name="Visible",
            email="visible@example.com",
            body="Visible comment",
            active=True,
        )
        Comment.objects.create(
            post=self.post,
            name="Hidden",
            email="hidden@example.com",
            body="Hidden comment",
            active=False,
        )
        response = self.client.get(self.post.get_absolute_url())
        self.assertContains(response, "Visible comment")
        self.assertNotContains(response, "Hidden comment")

    def test_comment_endpoint_is_post_only_and_redirects_after_success(self):
        url = reverse("blog:post_comment", args=[self.post.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(
            url,
            {"name": "Reader", "email": "reader@example.com", "body": "Nice"},
        )
        self.assertRedirects(
            response,
            f"{self.post.get_absolute_url()}#comments",
            fetch_redirect_response=False,
        )
        self.assertTrue(self.post.comments.filter(name="Reader").exists())

    def test_invalid_comment_is_redisplayed_without_being_saved(self):
        response = self.client.post(
            reverse("blog:post_comment", args=[self.post.pk]),
            {"name": "Reader", "email": "invalid", "body": "Nice"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Enter a valid email address", status_code=400)
        self.assertFalse(self.post.comments.filter(name="Reader").exists())


class AdminAccessTests(BlogTestBase):
    def test_admin_is_hidden_from_anonymous_users(self):
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 404)
        self.assertEqual(self.client.get(reverse("admin:login")).status_code, 404)

    def test_admin_is_hidden_from_authenticated_non_staff_users(self):
        self.client.force_login(self.author)

        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 404)
        self.assertEqual(self.client.get(reverse("admin:login")).status_code, 404)

    def test_admin_is_available_to_active_staff_users(self):
        self.author.is_staff = True
        self.author.save(update_fields=["is_staff"])
        self.client.force_login(self.author)

        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)


class UserAccountDefaultsTests(TestCase):
    def test_new_regular_user_receives_author_permissions(self):
        user = get_user_model().objects.create_user(
            username="new-author",
            password="test-password",
        )
        user = get_user_model().objects.get(pk=user.pk)

        self.assertTrue(user.has_perm("blog.view_post"))
        self.assertTrue(user.has_perm("blog.add_post"))
        self.assertTrue(user.has_perm("blog.change_post"))
        self.assertTrue(user.has_perm("blog.delete_post"))
        self.assertFalse(user.has_perm("blog.publish_post"))
        self.assertTrue(hasattr(user, "profile"))


class SignUpTests(TestCase):
    def test_signup_creates_and_logs_in_an_author(self):
        response = self.client.post(
            reverse("blog:signup"),
            {
                "username": "new-writer",
                "email": "writer@example.com",
                "password1": "Strong-Test-Passphrase-2026!",
                "password2": "Strong-Test-Passphrase-2026!",
            },
        )

        self.assertRedirects(response, reverse("blog:dashboard"))
        user = get_user_model().objects.get(username="new-writer")
        self.assertEqual(user.email, "writer@example.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertTrue(user.has_perm("blog.add_post"))
        self.assertTrue(user.has_perm("blog.change_post"))
        self.assertTrue(user.has_perm("blog.delete_post"))
        self.assertFalse(user.has_perm("blog.publish_post"))
        self.assertTrue(hasattr(user, "profile"))

    def test_signup_rejects_case_insensitive_duplicate_username(self):
        get_user_model().objects.create_user(
            username="ExistingWriter",
            password="Strong-Test-Passphrase-2026!",
        )

        response = self.client.post(
            reverse("blog:signup"),
            {
                "username": "existingwriter",
                "email": "another@example.com",
                "password1": "Another-Strong-Passphrase-2026!",
                "password2": "Another-Strong-Passphrase-2026!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with that username already exists.")
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_authenticated_user_is_redirected_away_from_signup(self):
        user = get_user_model().objects.create_user(
            username="signed-in-writer",
            password="Strong-Test-Passphrase-2026!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("blog:signup"))

        self.assertRedirects(response, reverse("blog:dashboard"))


class DashboardTests(BlogTestBase):
    def test_create_post_requires_login_and_add_permission(self):
        url = reverse("blog:create_post")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('blog:login')}?next={url}")

        self.client.force_login(self.author)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.author = self.login_with_permissions(self.author, "add_post")
        response = self.client.post(url, self.post_payload())
        self.assertRedirects(response, reverse("blog:dashboard"))
        created = Post.objects.get(title="New post")
        self.assertEqual(created.author, self.author)
        self.assertEqual(created.status, Post.Status.DRAFT)

    def test_author_without_publish_permission_can_only_create_drafts(self):
        self.author = self.login_with_permissions(self.author, "add_post")
        url = reverse("blog:create_post")

        form_response = self.client.get(url)
        self.assertNotContains(form_response, 'name="publish"')
        self.assertNotContains(form_response, "Publish / schedule")

        response = self.client.post(
            url,
            self.post_payload(title="Unauthorized publish", action="publish"),
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Post.objects.filter(title="Unauthorized publish").exists())

    def test_publish_permission_protects_existing_posts(self):
        self.author = self.login_with_permissions(self.author, "change_post")

        self.assertEqual(
            self.client.post(
                reverse("blog:post_publish", args=[self.draft.pk])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("blog:post_update", args=[self.post.pk])
            ).status_code,
            404,
        )
        draft_response = self.client.get(
            reverse("blog:post_update", args=[self.draft.pk])
        )
        self.assertEqual(draft_response.status_code, 200)
        self.assertNotContains(draft_response, 'name="publish"')

    def test_dashboard_requires_login_and_only_shows_the_authors_posts(self):
        other = get_user_model().objects.create_user(
            username="other", password="password"
        )
        Post.objects.create(title="Other post", body="Other", author=other)
        url = reverse("blog:dashboard")
        self.assertRedirects(
            self.client.get(url), f"{reverse('blog:login')}?next={url}"
        )

        self.client.force_login(self.author)
        response = self.client.get(url)
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.draft.title)
        self.assertContains(response, self.future.title)
        self.assertNotContains(response, "Other post")

    def test_preview_is_sanitized_and_does_not_save_a_post(self):
        self.author = self.login_with_permissions(self.author, "add_post")
        original_count = Post.objects.count()
        response = self.client.post(
            reverse("blog:create_post"),
            self.post_payload(
                title="Preview only",
                body="<script>alert(1)</script> **safe preview**",
                action="preview",
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>safe preview</strong>", html=True)
        self.assertNotIn("<script", str(response.context["preview_html"]))
        self.assertNotIn("alert(1)", str(response.context["preview_html"]))
        self.assertEqual(Post.objects.count(), original_count)

    def test_publish_action_supports_scheduled_posts(self):
        self.author = self.login_with_permissions(
            self.author,
            "add_post",
            "publish_post",
        )
        future_date = timezone.localtime() + timedelta(days=2)
        response = self.client.post(
            reverse("blog:create_post"),
            self.post_payload(
                title="New scheduled post",
                publish=future_date.strftime("%Y-%m-%dT%H:%M"),
                action="publish",
            ),
        )
        self.assertRedirects(response, reverse("blog:dashboard"))
        post = Post.objects.get(title="New scheduled post")
        self.assertEqual(post.status, Post.Status.PUBLISHED)
        self.assertEqual(post.publication_state, "Scheduled")
        self.assertNotIn(post, Post.published.all())

    def test_author_can_update_publish_and_unpublish_own_post(self):
        self.author = self.login_with_permissions(
            self.author,
            "change_post",
            "publish_post",
        )
        update_url = reverse("blog:post_update", args=[self.draft.pk])
        response = self.client.post(
            update_url,
            self.post_payload(
                title="Updated draft",
                body="Updated body",
                action="publish",
            ),
        )
        self.assertRedirects(response, reverse("blog:dashboard"))
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.title, "Updated draft")
        self.assertEqual(self.draft.status, Post.Status.PUBLISHED)

        unpublish_url = reverse("blog:post_unpublish", args=[self.draft.pk])
        self.assertEqual(self.client.get(unpublish_url).status_code, 405)
        self.assertRedirects(self.client.post(unpublish_url), reverse("blog:dashboard"))
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Post.Status.DRAFT)

    def test_author_cannot_manage_another_authors_post(self):
        other = get_user_model().objects.create_user(
            username="other", password="password"
        )
        other = self.login_with_permissions(
            other,
            "change_post",
            "delete_post",
            "publish_post",
        )
        self.assertEqual(
            self.client.get(
                reverse("blog:post_update", args=[self.draft.pk])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("blog:post_publish", args=[self.draft.pk])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("blog:post_delete", args=[self.draft.pk])
            ).status_code,
            404,
        )
        self.assertTrue(Post.objects.filter(pk=self.draft.pk).exists())

    def test_author_can_delete_own_post_with_permission(self):
        self.author = self.login_with_permissions(self.author, "delete_post")
        response = self.client.post(reverse("blog:post_delete", args=[self.draft.pk]))
        self.assertRedirects(response, reverse("blog:dashboard"))
        self.assertFalse(Post.objects.filter(pk=self.draft.pk).exists())


class AdminPermissionTests(BlogTestBase):
    def make_staff(self, *permissions):
        self.author.is_staff = True
        self.author.save(update_fields=["is_staff"])
        return self.login_with_permissions(self.author, *permissions)

    def test_admin_author_only_sees_own_posts(self):
        other = get_user_model().objects.create_user(
            username="other-admin-author",
            password="password",
        )
        other_post = Post.objects.create(
            title="Another author's private draft",
            body="Private",
            author=other,
        )
        self.make_staff("view_post", "change_post")

        response = self.client.get(reverse("admin:blog_post_changelist"))
        self.assertContains(response, self.draft.title)
        self.assertNotContains(response, other_post.title)
        self.assertNotEqual(
            self.client.get(
                reverse("admin:blog_post_change", args=[other_post.pk])
            ).status_code,
            200,
        )

    def test_admin_cannot_bypass_publish_permission(self):
        self.make_staff("add_post", "change_post", "view_post")
        add_url = reverse("admin:blog_post_add")
        response = self.client.post(
            add_url,
            {
                "title": "Admin-created draft",
                "slug": "admin-created-draft",
                "body": "Draft body",
                "tags": "django",
                "status": Post.Status.PUBLISHED,
                "publish": (timezone.localtime() + timedelta(days=2)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Post.objects.get(title="Admin-created draft")
        self.assertEqual(created.author, self.author)
        self.assertEqual(created.status, Post.Status.DRAFT)

        published_form = self.client.get(
            reverse("admin:blog_post_change", args=[self.post.pk])
        )
        self.assertEqual(published_form.status_code, 200)
        self.assertFalse(published_form.context["has_change_permission"])
        self.assertNotContains(published_form, 'name="_save"')
        self.assertNotContains(published_form, 'name="status"')
        draft_form = self.client.get(
            reverse("admin:blog_post_change", args=[self.draft.pk])
        )
        self.assertEqual(draft_form.status_code, 200)
        self.assertNotContains(draft_form, 'name="status"')
        self.assertNotContains(draft_form, 'name="publish"')

    def test_admin_publish_permission_exposes_publication_fields(self):
        self.make_staff("view_post", "change_post", "publish_post")
        response = self.client.get(
            reverse("admin:blog_post_change", args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="status"')
        self.assertContains(response, 'name="publish_0"')


class PublicInteractionTests(BlogTestBase):
    def test_share_requires_login_and_is_rate_limited(self):
        url = reverse("blog:post_share", args=[self.post.pk])
        self.assertRedirects(
            self.client.get(url),
            f"{reverse('blog:login')}?next={url}",
        )
        self.client.force_login(self.author)
        payload = {
            "name": "Reader",
            "email": "reader@example.com",
            "to": "friend@example.com",
            "comments": "Read this",
        }
        self.assertEqual(self.client.post(url, payload).status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        second_response = self.client.post(url, payload)
        self.assertContains(second_response, "Please wait", status_code=200)
        self.assertEqual(len(mail.outbox), 1)

    def test_share_reports_broker_failure_and_releases_throttle(self):
        self.client.force_login(self.author)
        url = reverse("blog:post_share", args=[self.post.pk])
        payload = {
            "name": "Reader",
            "email": "reader@example.com",
            "to": "friend@example.com",
            "comments": "Read this",
        }

        with patch(
            "blog.views.public.send_post_share_email.delay",
            side_effect=OperationalError("broker unavailable"),
        ):
            response = self.client.post(url, payload)

        self.assertContains(response, "temporarily unavailable", status_code=200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.client.post(url, payload).status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_profile_can_only_be_edited_by_its_owner(self):
        other = get_user_model().objects.create_user(
            username="other",
            password="test-password",
        )
        self.client.force_login(self.author)
        own_url = reverse("blog:edit-profile", args=[self.author.profile.pk])
        other_url = reverse("blog:edit-profile", args=[other.profile.pk])
        self.assertEqual(self.client.get(own_url).status_code, 200)
        self.assertEqual(self.client.get(other_url).status_code, 403)

    def test_feed_and_sitemap_only_contain_current_published_posts(self):
        feed_response = self.client.get(reverse("blog:post_feed"))
        self.assertContains(feed_response, self.post.title)
        self.assertNotContains(feed_response, self.draft.title)
        self.assertNotContains(feed_response, self.future.title)

        sitemap_response = self.client.get("/sitemap.xml")
        self.assertContains(sitemap_response, self.post.get_absolute_url())
        self.assertNotContains(sitemap_response, self.draft.get_absolute_url())
        self.assertNotContains(sitemap_response, self.future.get_absolute_url())


class SearchTests(BlogTestBase):
    def test_postgresql_full_text_search_only_returns_published_posts(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL full-text search requires PostgreSQL.")
        response = self.client.get(reverse("blog:post_search"), {"query": "Published"})
        self.assertContains(response, self.post.title)
        self.assertContains(response, "blog/css/pages/search.css")
        self.assertContains(response, "blog/js/infinite-scroll.js")
        self.assertNotContains(response, "blog/css/pages/post-list.css")
        self.assertNotContains(response, self.draft.title)

    def test_search_dialog_is_available_without_leaving_the_page(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertContains(response, 'id="searchDialog"')
        self.assertContains(response, reverse("blog:post_search_suggestions"))
        self.assertNotContains(
            response,
            f'href="{reverse("blog:post_search")}">Search</a>',
        )

    def test_search_suggestions_validate_short_queries_without_searching(self):
        with self.assertNumQueries(0):
            response = self.client.get(
                reverse("blog:post_search_suggestions"),
                {"q": "x"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Type at least two characters")
        cache_control = response.headers["Cache-Control"]
        self.assertIn("no-store", cache_control)
        self.assertIn("private", cache_control)

    def test_search_suggestions_are_limited_public_and_html_escaped(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL full-text search requires PostgreSQL.")

        unsafe = Post.objects.create(
            title='<img src=x onerror="alert(1)"> searchable',
            body="searchable content",
            author=self.author,
            status=Post.Status.PUBLISHED,
            publish=timezone.now() - timedelta(minutes=30),
        )
        for number in range(19):
            Post.objects.create(
                title=f"Searchable result {number}",
                body="searchable content",
                author=self.author,
                status=Post.Status.PUBLISHED,
                publish=timezone.now() - timedelta(minutes=number + 2),
            )

        with self.assertNumQueries(1):
            response = self.client.get(
                reverse("blog:post_search_suggestions"),
                {"q": "searchable"},
            )
        self.assertEqual(len(response.context["results"]), 8)
        self.assertTrue(response.context["has_more"])
        self.assertContains(response, "View all results")
        self.assertNotContains(response, self.draft.title)
        if unsafe in response.context["results"]:
            self.assertNotContains(response, '<img src=x onerror="alert(1)">')
            self.assertContains(response, "&lt;img")

        full_page = self.client.get(
            reverse("blog:post_search"),
            {"query": "searchable"},
        )
        self.assertContains(full_page, 'id="searchPageResults"')

        with self.assertNumQueries(1):
            first_page = self.client.get(
                reverse("blog:post_search"),
                {"query": "searchable"},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(len(first_page.context["results"]), 10)
        self.assertEqual(first_page.context["next_page"], 2)
        self.assertContains(first_page, "Load more")

        first_page_ids = {post.pk for post in first_page.context["results"]}
        with self.assertNumQueries(1):
            second_page = self.client.get(
                reverse("blog:post_search"),
                {"query": "searchable", "page": 2},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        second_page_ids = {post.pk for post in second_page.context["results"]}
        self.assertEqual(len(second_page_ids), 10)
        self.assertTrue(first_page_ids.isdisjoint(second_page_ids))
        self.assertIsNone(second_page.context["next_page"])
        self.assertNotContains(second_page, "<html")
        self.assertNotContains(second_page, "Load more")


class PostModelTests(BlogTestBase):
    def test_slug_generation_handles_unicode_and_same_day_duplicates(self):
        duplicate = Post.objects.create(
            title=self.post.title,
            body="Duplicate",
            author=self.author,
            publish=self.post.publish,
        )
        arabic = Post.objects.create(
            title="مقال جديد",
            body="Arabic",
            author=self.author,
        )
        self.assertEqual(duplicate.slug, "published-post-2")
        self.assertEqual(arabic.slug, "مقال-جديد")

        another_day = Post.objects.create(
            title=self.post.title,
            body="Another date",
            author=self.author,
            publish=self.post.publish + timedelta(days=2),
        )
        self.assertEqual(another_day.slug, "published-post-3")


class MarkdownSecurityTests(TestCase):
    def test_markdown_removes_scripts_event_handlers_and_unsafe_urls(self):
        rendered = str(
            render_markdown(
                '<script>alert(1)</script><img src=x onerror="alert(2)"> '
                "[unsafe](javascript:alert(3)) **safe**"
            )
        )
        self.assertNotIn("<script", rendered)
        self.assertNotIn("<img", rendered)
        self.assertNotIn("javascript:", rendered)
        self.assertNotIn("onerror", rendered)
        self.assertIn("<strong>safe</strong>", rendered)
