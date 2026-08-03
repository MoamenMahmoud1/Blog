from django.shortcuts import redirect


def page_not_found(request, exception):
    return redirect("blog:dashboard")
