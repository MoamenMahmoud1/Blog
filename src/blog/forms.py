from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Comment, Post, Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")

    def clean_username(self):
        username = super().clean_username()
        if self._meta.model.objects.filter(username__iexact=username).exists():
            raise ValidationError("A user with that username already exists.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self._meta.model.objects.normalize_email(
            self.cleaned_data["email"]
        )
        if commit:
            user.save()
        return user


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "body", "tags", "publish"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 14}),
            "publish": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, can_publish=False, **kwargs):
        super().__init__(*args, **kwargs)
        if can_publish:
            self.fields["publish"].input_formats = ["%Y-%m-%dT%H:%M"]
        else:
            self.fields.pop("publish")

    def clean_title(self):
        return " ".join(self.cleaned_data["title"].splitlines()).strip()

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise ValidationError("The post body cannot be empty.")
        return body


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=80)
    email = forms.EmailField()
    to = forms.EmailField(label="Recipient email")
    comments = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].splitlines()).strip()


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["name", "email", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 5})}

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if len(body) > 5000:
            raise ValidationError("Comments cannot exceed 5,000 characters.")
        return body


class SearchForm(forms.Form):
    query = forms.CharField(min_length=2, max_length=200, strip=True)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["img"]
        widgets = {
            "img": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def clean_img(self):
        image = self.cleaned_data.get("img")
        if image and image.size > 5 * 1024 * 1024:
            raise ValidationError("Profile images cannot exceed 5 MB.")
        return image
