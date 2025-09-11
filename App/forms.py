from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Profile, Post

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["avatar", "bio", "location", "phone", "birth_date"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows":4, "placeholder":"Tell something about you..."}),
            "location": forms.TextInput(attrs={"placeholder":"City, Country"}),
            "phone": forms.TextInput(attrs={"placeholder":"Phone number"}),
            "birth_date": forms.DateInput(attrs={"type":"date"}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content", "image"]  # include image
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Enter title"}),
            "content": forms.Textarea(attrs={"placeholder": "Write your post..."}),
        }
