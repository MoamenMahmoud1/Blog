from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import ListView

from ..forms import SearchForm
from ..pagination import parse_page_number
from ..selectors import search_batch


class PostSearchView(ListView):
    context_object_name = "results"
    template_name = "post/search.html"
    page_size = 10
    max_page = 1000

    def get_template_names(self):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return ["post/includes/search_page_results.html"]
        return [self.template_name]

    def get_queryset(self):
        self.form = SearchForm(self.request.GET or None)
        self.query = None
        self.next_page = None
        if not self.form.is_valid():
            return []

        self.query = self.form.cleaned_data["query"]
        page = parse_page_number(
            self.request.GET.get("page", 1),
            max_page=self.max_page,
        )
        results, has_more = search_batch(
            self.query,
            page=page,
            page_size=self.page_size,
            max_page=self.max_page,
        )
        if has_more:
            self.next_page = page + 1
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "form": self.form,
                "query": self.query,
                "next_page": self.next_page,
            }
        )
        return context


@method_decorator(never_cache, name="dispatch")
class PostSearchSuggestionsView(ListView):
    context_object_name = "results"
    template_name = "blog/includes/search_results.html"
    http_method_names = ["get"]
    result_limit = 8

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()[:200]
        self.form = SearchForm({"query": self.query})
        self.has_more = False
        if not self.form.is_valid():
            return []

        self.query = self.form.cleaned_data["query"]
        results, self.has_more = search_batch(
            self.query,
            page=1,
            page_size=self.result_limit,
        )
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "query": self.query,
                "query_is_valid": self.form.is_valid(),
                "has_more": self.has_more,
            }
        )
        return context
