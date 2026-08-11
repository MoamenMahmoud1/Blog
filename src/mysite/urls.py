from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from blog.sitemaps import PostSitemap
from mysite.health import LivenessView, ReadinessView
from mysite.media import PublicProfileMediaView

sitemaps = {
    "posts": PostSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live/", LivenessView.as_view(), name="health-live"),
    path("presentations/", include("presentation.urls")),
    path("health/ready/", ReadinessView.as_view(), name="health-ready"),
    path(
        "media/profiles/<path:path>",
        PublicProfileMediaView.as_view(),
        name="public-profile-media",
    ),
    path("blog/", include("blog.urls", namespace="blog")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )


handler404 = "mysite.views.page_not_found"
