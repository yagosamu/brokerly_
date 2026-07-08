from django import forms

from renewals.models import Renewal


class RenewalForm(forms.ModelForm):
    class Meta:
        model = Renewal
        fields = ('status', 'notes')
        labels = {
            'status': 'Status',
            'notes': 'Observações',
        }


class RenewalSearchForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os status')] + list(Renewal.Status.choices),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )


class RenewPolicyForm(forms.Form):
    new_policy_number = forms.CharField(
        label='Número da nova apólice',
        max_length=40,
    )
