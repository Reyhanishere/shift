from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ShiftRequest,NurseProfile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ShiftRequestForm(forms.ModelForm):
    class Meta:
        model = ShiftRequest
        fields = ['shift', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

class NurseProfileForm(forms.ModelForm):
    class Meta:
        model = NurseProfile
        fields = ['full_name', 'position']