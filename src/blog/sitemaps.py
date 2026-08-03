from django.contrib.sitemaps import Sitemap

from .models import Post


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Post.published.only("slug", "publish", "updated")

    def lastmod(self, obj):
        return obj.updated
