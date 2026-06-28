import re

from django import forms
from validate_docbr import CNPJ, CPF

from clients.models import Client


DIGITS_RE = re.compile(r'\D')


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = (
            'person_type',
            'name',
            'trade_name',
            'document',
            'email',
            'phone',
            'birth_date',
            'address_line',
            'address_number',
            'address_complement',
            'district',
            'city',
            'state',
            'zip_code',
            'notes',
            'is_active',
        )
        labels = {
            'person_type': 'Tipo de pessoa',
            'name': 'Nome / Razão social',
            'trade_name': 'Nome fantasia',
            'document': 'CPF / CNPJ',
            'email': 'E-mail',
            'phone': 'Telefone',
            'birth_date': 'Data de nascimento',
            'address_line': 'Logradouro',
            'address_number': 'Número',
            'address_complement': 'Complemento',
            'district': 'Bairro',
            'city': 'Cidade',
            'state': 'UF',
            'zip_code': 'CEP',
            'notes': 'Observações',
            'is_active': 'Cliente ativo',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'state': forms.TextInput(attrs={'maxlength': 2}),
        }

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)

    def clean_document(self):
        raw_document = self.cleaned_data['document']
        digits = DIGITS_RE.sub('', raw_document)
        person_type = (
            self.cleaned_data.get('person_type')
            or self.data.get('person_type')
        )

        if person_type == Client.PersonType.NATURAL:
            validator = CPF()
            if not validator.validate(digits):
                raise forms.ValidationError('CPF inválido.')
            formatted_document = validator.mask(digits)
        elif person_type == Client.PersonType.LEGAL:
            validator = CNPJ()
            if not validator.validate(digits):
                raise forms.ValidationError('CNPJ inválido.')
            formatted_document = validator.mask(digits)
        else:
            raise forms.ValidationError('Tipo de pessoa inválido.')

        if self.brokerage is not None:
            queryset = Client.objects.filter(
                brokerage=self.brokerage,
                document=formatted_document,
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError(
                    'Já existe um cliente com este documento na sua corretora.'
                )
        return formatted_document

    def clean(self):
        cleaned_data = super().clean()
        if (
            self.brokerage is not None
            and not self.instance.pk
            and cleaned_data.get('is_active', True)
        ):
            max_clients = self.brokerage.plan.max_clients
            if max_clients is not None:
                active_clients = Client.objects.filter(
                    brokerage=self.brokerage,
                    is_active=True,
                ).count()
                if active_clients >= max_clients:
                    raise forms.ValidationError(
                        f'Limite do plano atingido: {max_clients} clientes ativos.'
                    )
        return cleaned_data


class ClientSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'Buscar nome, documento ou e-mail'}
        ),
    )
    person_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(Client.PersonType.choices),
    )
