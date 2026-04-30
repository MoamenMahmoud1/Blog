from django import forms
from .models import Comment , Profile

#====================================================================
class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False , widget=forms.Textarea)
    
    
    
#==========================================
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields =  ["name" , "email" , "body"]
        
        
class SearchForm(forms.Form):
    query = forms.CharField()




class ProfileForm(forms.ModelForm):
    class Meta:

        model = Profile
        fields = ["img"]
    img = forms.ImageField(
        widget=forms.FileInput
    )
        #widgets = {
        #    'img': forms.ClearableFileInput(attrs={
        #        'class':'form-control'
        #    })
        #}
    