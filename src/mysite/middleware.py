from django.http import Http404


class HideAdminFromUnauthorizedUsersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        resolver_match = request.resolver_match
        if resolver_match is None or resolver_match.namespace != "admin":
            return None

        user = request.user
        if not user.is_authenticated or not user.is_active:
            raise Http404
        if not (user.is_staff or user.is_superuser):
            raise Http404

        return None
