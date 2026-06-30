import json

from django import forms

from claims.models import Claim
from insurance.models import CoveredItem, Policy


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = (
            'claim_number',
            'policy',
            'covered_item',
            'occurrence_date',
            'notice_date',
            'status',
            'description',
            'claimed_amount',
            'approved_amount',
        )
        labels = {
            'claim_number': 'Número do sinistro',
            'policy': 'Apólice',
            'covered_item': 'Item coberto',
            'occurrence_date': 'Data da ocorrência',
            'notice_date': 'Data do aviso',
            'status': 'Status',
            'description': 'Descrição',
            'claimed_amount': 'Valor reclamado (R$)',
            'approved_amount': 'Valor aprovado (R$)',
        }
        widgets = {
            'occurrence_date': forms.DateInput(attrs={'type': 'date'}),
            'notice_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)
        if brokerage is not None:
            self.fields['policy'].queryset = Policy.objects.filter(
                brokerage=brokerage,
            ).select_related('client', 'insurer').order_by('-created_at')
            self.fields['covered_item'].queryset = CoveredItem.objects.filter(
                brokerage=brokerage,
                policy__isnull=False,
            ).select_related('policy').order_by('description')

    def clean_claim_number(self):
        value = self.cleaned_data['claim_number'].strip()
        if self.brokerage is None:
            return value
        queryset = Claim.objects.filter(
            brokerage=self.brokerage,
            claim_number=value,
        )
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(
                'Já existe um sinistro com este número na sua corretora.'
            )
        return value

    def clean(self):
        cleaned_data = super().clean()
        policy = cleaned_data.get('policy')
        covered_item = cleaned_data.get('covered_item')
        occurrence_date = cleaned_data.get('occurrence_date')
        notice_date = cleaned_data.get('notice_date')

        if policy and covered_item and covered_item.policy_id != policy.id:
            self.add_error(
                'covered_item',
                'O item coberto selecionado não pertence à apólice escolhida.',
            )

        if (
            covered_item
            and self.brokerage
            and covered_item.brokerage_id != self.brokerage.id
        ):
            self.add_error('covered_item', 'Item coberto inválido.')
        if (
            policy
            and self.brokerage
            and policy.brokerage_id != self.brokerage.id
        ):
            self.add_error('policy', 'Apólice inválida.')

        if occurrence_date and notice_date and occurrence_date > notice_date:
            self.add_error(
                'occurrence_date',
                'Ocorrência não pode ser depois do aviso.',
            )

        claimed_amount = cleaned_data.get('claimed_amount') or 0
        approved_amount = cleaned_data.get('approved_amount') or 0
        if approved_amount > claimed_amount:
            self.add_error(
                'approved_amount',
                'Valor aprovado não pode exceder o valor reclamado.',
            )

        return cleaned_data

    @property
    def policy_to_items_json(self):
        """Map policy IDs to covered item choices for the dynamic form."""
        queryset = self.fields['covered_item'].queryset
        data = {}
        for item in queryset:
            key = str(item.policy_id)
            label = item.description
            if item.identifier:
                label = f'{label} · {item.identifier}'
            data.setdefault(key, []).append(
                {
                    'id': item.id,
                    'label': label,
                }
            )
        return json.dumps(data, ensure_ascii=False)


class ClaimSearchForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os status')] + list(Claim.Status.choices),
    )
    policy = forms.ModelChoiceField(
        required=False,
        queryset=Policy.objects.none(),
        empty_label='Todas as apólices',
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
            self.fields['policy'].queryset = Policy.objects.filter(
                brokerage=brokerage,
            ).order_by('-created_at')
