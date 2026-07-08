from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    UserCreationForm,
)
from django.template import loader

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


class MemberCreateForm(UserCreationForm):
    email = forms.EmailField(label='E-mail')
    first_name = forms.CharField(label='Nome', max_length=150)
    last_name = forms.CharField(label='Sobrenome', max_length=150)
    role = forms.ChoiceField(
        label='Perfil de acesso',
        choices=User.Role.choices,
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role')

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.brokerage is None:
            raise forms.ValidationError('Corretora não identificada.')

        plan = self.brokerage.plan
        if plan.max_users is not None:
            current_users = User.objects.filter(
                brokerage=self.brokerage,
                is_active=True,
            ).count()
            if current_users >= plan.max_users:
                raise forms.ValidationError(
                    f'Limite do plano atingido: {plan.max_users} usuários ativos.'
                )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.brokerage = self.brokerage
        if commit:
            user.save()
        return user


class MemberUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role', 'is_active')
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
            'role': 'Perfil de acesso',
            'is_active': 'Conta ativa',
        }

    def __init__(self, *args, requesting_user=None, **kwargs):
        self.requesting_user = requesting_user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if (
            self.instance.role == User.Role.OWNER
            and cleaned_data.get('role') != User.Role.OWNER
            and (
                self.requesting_user is None
                or self.requesting_user.role != User.Role.OWNER
            )
        ):
            raise forms.ValidationError(
                'Apenas o próprio administrador pode alterar o perfil de Administrador.'
            )
        if (
            self.instance.role == User.Role.OWNER
            and cleaned_data.get('is_active') is False
        ):
            raise forms.ValidationError(
                'O administrador da corretora não pode ser desativado.'
            )
        return cleaned_data


class AsyncPasswordResetForm(PasswordResetForm):
    """PasswordResetForm que enfileira o envio via Celery."""

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        from notifications.tasks import send_password_reset_email

        subject = loader.render_to_string(
            subject_template_name,
            context,
        ).strip().replace('\n', ' ')
        body = loader.render_to_string(email_template_name, context)
        html_body = None
        if html_email_template_name:
            html_body = loader.render_to_string(
                html_email_template_name,
                context,
            )

        send_password_reset_email.delay(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[to_email],
            html_body=html_body,
        )
