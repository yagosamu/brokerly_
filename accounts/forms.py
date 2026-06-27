from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )
    first_name = forms.CharField(label='Nome', max_length=150)
    last_name = forms.CharField(label='Sobrenome', max_length=150)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')


class EmailAuthenticationForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields['username'].label = 'E-mail'
        self.fields['username'].widget = forms.EmailInput(
            attrs={
                'autofocus': True,
                'autocomplete': 'email',
            },
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
