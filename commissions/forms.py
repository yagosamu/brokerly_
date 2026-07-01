from decimal import Decimal

from django import forms

from commissions.models import Commission, CommissionSplit
from commissions.services import calculate_split_amount
from partners.models import Agent, Producer


class CommissionStatusForm(forms.ModelForm):
    class Meta:
        model = Commission
        fields = ('status', 'received_at', 'paid_at')
        labels = {
            'status': 'Status',
            'received_at': 'Data de recebimento',
            'paid_at': 'Data de repasse',
        }
        widgets = {
            'received_at': forms.DateInput(attrs={'type': 'date'}),
            'paid_at': forms.DateInput(attrs={'type': 'date'}),
        }


class CommissionSplitForm(forms.ModelForm):
    class Meta:
        model = CommissionSplit
        fields = (
            'beneficiary_type',
            'agent',
            'producer',
            'rate',
            'amount',
            'status',
            'paid_at',
        )
        labels = {
            'beneficiary_type': 'Tipo de beneficiário',
            'agent': 'Agente',
            'producer': 'Produtor',
            'rate': 'Taxa de repasse',
            'amount': 'Valor do repasse',
            'status': 'Status',
            'paid_at': 'Data de pagamento',
        }
        widgets = {
            'paid_at': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(
        self,
        *args,
        brokerage=None,
        commission=None,
        **kwargs,
    ):
        self.brokerage = brokerage
        self.commission = commission
        super().__init__(*args, **kwargs)
        self.fields['agent'].queryset = Agent.objects.none()
        self.fields['producer'].queryset = Producer.objects.none()
        if brokerage is not None:
            self.fields['agent'].queryset = Agent.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')
            self.fields['producer'].queryset = Producer.objects.filter(
                brokerage=brokerage,
                is_active=True,
            ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        beneficiary_type = cleaned_data.get('beneficiary_type')
        agent = cleaned_data.get('agent')
        producer = cleaned_data.get('producer')
        rate = cleaned_data.get('rate') or Decimal('0')
        amount = cleaned_data.get('amount') or Decimal('0')

        if beneficiary_type == CommissionSplit.BeneficiaryType.AGENT:
            if agent is None:
                self.add_error('agent', 'Selecione um agente.')
            if producer is not None:
                self.add_error(
                    'producer',
                    'Não selecione um produtor para um repasse de agente.',
                )
        elif beneficiary_type == CommissionSplit.BeneficiaryType.PRODUCER:
            if producer is None:
                self.add_error('producer', 'Selecione um produtor.')
            if agent is not None:
                self.add_error(
                    'agent',
                    'Não selecione um agente para um repasse de produtor.',
                )

        if rate > 0 and amount == 0 and self.commission is not None:
            amount = calculate_split_amount(self.commission, rate)
            cleaned_data['amount'] = amount

        if self.commission is not None:
            splits = self.commission.splits.all()
            if self.instance.pk:
                splits = splits.exclude(pk=self.instance.pk)
            existing_amount = sum(
                (split.amount for split in splits),
                start=Decimal('0'),
            )
            if existing_amount + amount > self.commission.insurer_amount:
                raise forms.ValidationError(
                    'A soma dos repasses não pode exceder a comissão recebida.'
                )

        return cleaned_data


class CommissionSearchForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os status')] + list(Commission.Status.choices),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
