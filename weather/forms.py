from django import forms
class UploadCSVForm(forms.Form):
    csv_file = forms.FileField()

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username','email','password1','password2')
