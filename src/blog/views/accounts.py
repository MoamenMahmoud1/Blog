from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from ..forms import ProfileForm, SignUpForm
from ..models import Profile


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("blog:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("blog:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Your account is ready. Welcome to My Blog!")
        return response


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    context_object_name = "profile"
    template_name = "accounts/profile.html"

    def get_queryset(self):
        return Profile.objects.select_related("user")

    def get_object(self, queryset=None):
        if not hasattr(self, "_profile_object"):
            self._profile_object = super().get_object(queryset)
        return self._profile_object

    def test_func(self):
        return self.request.user == self.get_object().user

    def get_success_url(self):
        return reverse("blog:edit-profile", kwargs={"pk": self.object.pk})


class LoginView(DjangoLoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("blog:post_list")


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy("blog:post_list")
