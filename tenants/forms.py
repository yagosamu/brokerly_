import re

from django import forms

from tenants.models import Brokerage


CNPJ_RE = re.compile(r'\D')


class BrokerageOnboardingForm(forms.ModelForm):
    class Meta:
        model = Brokerage
        fields = ('legal_name', 'trade_name', 'cnpj', 'email', 'phone')
        labels = {
            'legal_name': 'Razão social',
            'trade_name': 'Nome fantasia',
            'cnpj': 'CNPJ',
            'email': 'E-mail',
            'phone': 'Telefone',
        }
        widgets = {
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'autocomplete': 'tel'}),
        }

    def clean_cnpj(self):
        raw = self.cleaned_data['cnpj']
        digits = CNPJ_RE.sub('', raw)
        if len(digits) != 14:
            raise forms.ValidationError('CNPJ deve conter 14 dígitos.')

        formatted = (
            f'{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/'
            f'{digits[8:12]}-{digits[12:14]}'
        )
        if Brokerage.objects.filter(cnpj=formatted).exists():
            raise forms.ValidationError(
                'Já existe uma corretora cadastrada com este CNPJ.'
            )
        return formatted
