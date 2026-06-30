from django import forms
from django.forms import inlineformset_factory

from clients.models import Client
from insurance.models import CoveredItem, Policy, Proposal
from insurers.models import Insurer, LineOfBusiness


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = (
            'number',
            'client',
            'insurer',
            'line_of_business',
            'status',
            'net_premium',
            'total_premium',
            'iof',
            'proposed_start_date',
            'proposed_end_date',
            'payment_terms',
            'notes',
        )
        labels = {
            'number': 'Número da proposta',
            'client': 'Cliente',
            'insurer': 'Seguradora',
            'line_of_business': 'Ramo',
            'status': 'Status',
            'net_premium': 'Prêmio líquido (R$)',
            'total_premium': 'Prêmio total (R$)',
            'iof': 'IOF (R$)',
            'proposed_start_date': 'Início da vigência',
            'proposed_end_date': 'Fim da vigência',
            'payment_terms': 'Forma de pagamento',
            'notes': 'Observações',
        }
        widgets = {
            'proposed_start_date': forms.DateInput(attrs={'type': 'date'}),
            'proposed_end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)
        if brokerage is not None:
            self.fields['client'].queryset = Client.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')
            self.fields['insurer'].queryset = Insurer.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')
            self.fields['line_of_business'].queryset = (
                LineOfBusiness.objects.filter(
                    brokerage=brokerage,
                    is_active=True,
                ).order_by('name')
            )

    def clean_number(self):
        number = self.cleaned_data['number'].strip()
        if self.brokerage is None:
            return number
        queryset = Proposal.objects.filter(
            brokerage=self.brokerage,
            number=number,
        )
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(
                'Já existe uma proposta com este número na sua corretora.'
            )
        return number


class CoveredItemForm(forms.ModelForm):
    class Meta:
        model = CoveredItem
        fields = (
            'item_type',
            'description',
            'identifier',
            'insured_amount',
            'attributes',
            'coverages',
        )
        labels = {
            'item_type': 'Tipo',
            'description': 'Descrição',
            'identifier': 'Identificador',
            'insured_amount': 'Importância segurada (R$)',
            'attributes': 'Atributos (JSON)',
            'coverages': 'Coberturas (JSON)',
        }
        widgets = {
            'attributes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '{"ano": 2024, "modelo": "X"}',
                }
            ),
            'coverages': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '[{"nome":"Colisão","limite":50000}]',
                }
            ),
        }


CoveredItemFormSet = inlineformset_factory(
    Proposal,
    CoveredItem,
    form=CoveredItemForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class ProposalSearchForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os status')] + list(Proposal.Status.choices),
    )
    insurer = forms.ModelChoiceField(
        required=False,
        queryset=Insurer.objects.none(),
        empty_label='Todas as seguradoras',
    )
    line_of_business = forms.ModelChoiceField(
        required=False,
        queryset=LineOfBusiness.objects.none(),
        empty_label='Todos os ramos',
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, brokerage=None, **kwargs):
        super().__init__(*args, **kwargs)
        if brokerage is not None:
            self.fields['insurer'].queryset = Insurer.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')
            self.fields['line_of_business'].queryset = (
                LineOfBusiness.objects.filter(
                    brokerage=brokerage,
                    is_active=True,
                ).order_by('name')
            )


class PolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = (
            'policy_number',
            'client',
            'insurer',
            'line_of_business',
            'status',
            'net_premium',
            'total_premium',
            'iof',
            'commission_rate',
            'start_date',
            'end_date',
            'payment_info',
        )
        labels = {
            'policy_number': 'Número da apólice',
            'client': 'Cliente',
            'insurer': 'Seguradora',
            'line_of_business': 'Ramo',
            'status': 'Status',
            'net_premium': 'Prêmio líquido (R$)',
            'total_premium': 'Prêmio total (R$)',
            'iof': 'IOF (R$)',
            'commission_rate': 'Taxa de comissão',
            'start_date': 'Início da vigência',
            'end_date': 'Fim da vigência',
            'payment_info': 'Forma de pagamento',
        }
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)
        if brokerage is not None:
            self.fields['client'].queryset = Client.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')
            self.fields['insurer'].queryset = Insurer.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')
            self.fields['line_of_business'].queryset = (
                LineOfBusiness.objects.filter(
                    brokerage=brokerage,
                    is_active=True,
                ).order_by('name')
            )

    def clean_policy_number(self):
        policy_number = self.cleaned_data['policy_number'].strip()
        if self.brokerage is None:
            return policy_number
        queryset = Policy.objects.filter(
            brokerage=self.brokerage,
            policy_number=policy_number,
        )
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(
                'Já existe uma apólice com este número na sua corretora.'
            )
        return policy_number


class PolicySearchForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os status')] + list(Policy.Status.choices),
    )
    insurer = forms.ModelChoiceField(
        required=False,
        queryset=Insurer.objects.none(),
        empty_label='Todas as seguradoras',
    )
    line_of_business = forms.ModelChoiceField(
        required=False,
        queryset=LineOfBusiness.objects.none(),
        empty_label='Todos os ramos',
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, brokerage=None, **kwargs):
        super().__init__(*args, **kwargs)
        if brokerage is not None:
            self.fields['insurer'].queryset = Insurer.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')
            self.fields['line_of_business'].queryset = (
                LineOfBusiness.objects.filter(
                    brokerage=brokerage,
                    is_active=True,
                ).order_by('name')
            )
