from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=20, required=True)

    class Meta:
        model = CustomUser
        fields = ('phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.phone_number = self.cleaned_data['phone_number']
        if commit:
            user.save()
        return user
