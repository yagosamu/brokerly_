import re

from django import forms
from validate_docbr import CNPJ

from insurers.models import Insurer, LineOfBusiness


DIGITS_RE = re.compile(r'\D')


class InsurerForm(forms.ModelForm):
    class Meta:
        model = Insurer
        fields = ('name', 'cnpj', 'susep_code', 'email', 'phone', 'is_active')
        labels = {
            'name': 'Razão social',
            'cnpj': 'CNPJ',
            'susep_code': 'Código SUSEP',
            'email': 'E-mail',
            'phone': 'Telefone',
            'is_active': 'Seguradora ativa',
        }

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)

    def clean_cnpj(self):
        raw_cnpj = self.cleaned_data['cnpj']
        digits = DIGITS_RE.sub('', raw_cnpj)
        validator = CNPJ()
        if not validator.validate(digits):
            raise forms.ValidationError('CNPJ inválido.')
        return validator.mask(digits)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if self.brokerage is None:
            return name
        queryset = Insurer.objects.filter(
            brokerage=self.brokerage,
            name__iexact=name,
        )
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(
                'Já existe uma seguradora com este nome na sua corretora.'
            )
        return name


class InsurerSearchForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('active', 'Ativas'), ('inactive', 'Inativas')],
    )


class LineOfBusinessForm(forms.ModelForm):
    class Meta:
        model = LineOfBusiness
        fields = ('name', 'code', 'category', 'is_active')
        labels = {
            'name': 'Nome do ramo',
            'code': 'Código SUSEP',
            'category': 'Categoria',
            'is_active': 'Ramo ativo',
        }

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if self.brokerage is None:
            return name
        queryset = LineOfBusiness.objects.filter(
            brokerage=self.brokerage,
            name__iexact=name,
        )
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(
                'Já existe um ramo com este nome na sua corretora.'
            )
        return name


class LineOfBusinessSearchForm(forms.Form):
    q = forms.CharField(required=False)
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas')] + list(LineOfBusiness.Category.choices),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('active', 'Ativos'), ('inactive', 'Inativos')],
    )
