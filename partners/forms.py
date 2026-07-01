import re

from django import forms
from django.contrib.auth import get_user_model
from validate_docbr import CNPJ, CPF

from partners.models import Agent, EntityType, Producer


DIGITS_RE = re.compile(r'\D')
User = get_user_model()


def validate_document(raw_document, entity_type):
    digits = DIGITS_RE.sub('', raw_document)
    if entity_type == EntityType.COMPANY:
        validator = CNPJ()
        invalid_message = 'CNPJ inválido.'
        expected_length = 14
    else:
        validator = CPF()
        invalid_message = 'CPF inválido.'
        expected_length = 11
    if len(digits) != expected_length or not validator.validate(digits):
        raise forms.ValidationError(invalid_message)
    return validator.mask(digits)


class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = (
            'entity_type',
            'name',
            'document',
            'email',
            'phone',
            'susep_code',
            'user',
            'default_commission_rate',
            'is_active',
        )
        labels = {
            'entity_type': 'Tipo de pessoa',
            'name': 'Nome',
            'document': 'CPF/CNPJ',
            'email': 'E-mail',
            'phone': 'Telefone',
            'susep_code': 'Código SUSEP',
            'user': 'Usuário vinculado',
            'default_commission_rate': 'Taxa padrão de comissão',
            'is_active': 'Agente ativo',
        }

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.none()
        if brokerage is not None:
            self.fields['user'].queryset = User.objects.filter(
                brokerage=brokerage,
            ).order_by('email')

    def clean_document(self):
        document = validate_document(
            self.cleaned_data['document'],
            self.cleaned_data.get('entity_type'),
        )
        if self.brokerage is None:
            return document
        queryset = Agent.objects.filter(
            brokerage=self.brokerage,
            document=document,
        )
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(
                'Já existe um agente com este documento na sua corretora.'
            )
        return document


class AgentSearchForm(forms.Form):
    q = forms.CharField(required=False)
    entity_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os tipos')] + list(EntityType.choices),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('active', 'Ativos'), ('inactive', 'Inativos')],
    )

    def __init__(self, *args, brokerage=None, **kwargs):
        super().__init__(*args, **kwargs)


class ProducerForm(forms.ModelForm):
    class Meta:
        model = Producer
        fields = (
            'agent',
            'entity_type',
            'name',
            'document',
            'email',
            'phone',
            'user',
            'default_commission_rate',
            'is_active',
        )
        labels = {
            'agent': 'Agente',
            'entity_type': 'Tipo de pessoa',
            'name': 'Nome',
            'document': 'CPF/CNPJ',
            'email': 'E-mail',
            'phone': 'Telefone',
            'user': 'Usuário vinculado',
            'default_commission_rate': 'Taxa padrão de comissão',
            'is_active': 'Produtor ativo',
        }

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)
        self.fields['agent'].queryset = Agent.objects.none()
        self.fields['user'].queryset = User.objects.none()
        if brokerage is not None:
            self.fields['agent'].queryset = Agent.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')
            self.fields['user'].queryset = User.objects.filter(
                brokerage=brokerage,
            ).order_by('email')

    def clean_document(self):
        document = validate_document(
            self.cleaned_data['document'],
            self.cleaned_data.get('entity_type'),
        )
        if self.brokerage is None:
            return document
        queryset = Producer.objects.filter(
            brokerage=self.brokerage,
            document=document,
        )
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(
                'Já existe um produtor com este documento na sua corretora.'
            )
        return document

    def clean(self):
        cleaned_data = super().clean()
        agent = cleaned_data.get('agent')
        if (
            agent
            and self.brokerage
            and agent.brokerage_id != self.brokerage.id
        ):
            self.add_error('agent', 'Agente inválido.')
        return cleaned_data


class ProducerSearchForm(forms.Form):
    q = forms.CharField(required=False)
    entity_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os tipos')] + list(EntityType.choices),
    )
    agent = forms.ModelChoiceField(
        required=False,
        queryset=Agent.objects.none(),
        empty_label='Todos os agentes',
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('active', 'Ativos'), ('inactive', 'Inativos')],
    )

    def __init__(self, *args, brokerage=None, **kwargs):
        super().__init__(*args, **kwargs)
        if brokerage is not None:
            self.fields['agent'].queryset = Agent.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')
