from django import forms
from django.forms import inlineformset_factory

from clients.models import Client
from crm.models import Deal, Pipeline, Stage
from insurance.models import Proposal
from insurers.models import Insurer, LineOfBusiness
from partners.models import Agent, Producer


class PipelineForm(forms.ModelForm):
    class Meta:
        model = Pipeline
        fields = ('name', 'is_default')
        labels = {
            'name': 'Nome',
            'is_default': 'Pipeline padrão',
        }


class StageForm(forms.ModelForm):
    class Meta:
        model = Stage
        fields = ('name', 'color', 'order', 'is_won', 'is_lost')
        labels = {
            'name': 'Nome',
            'color': 'Cor',
            'order': 'Ordem',
            'is_won': 'Etapa de ganho',
            'is_lost': 'Etapa de perda',
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_won') and cleaned_data.get('is_lost'):
            raise forms.ValidationError(
                'A etapa não pode ser marcada como ganha e perdida ao mesmo tempo.'
            )
        return cleaned_data


StageFormSet = inlineformset_factory(
    Pipeline,
    Stage,
    form=StageForm,
    extra=1,
    can_delete=True,
)


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = (
            'pipeline',
            'stage',
            'client',
            'producer',
            'agent',
            'line_of_business',
            'insurer',
            'proposal',
            'title',
            'description',
            'estimated_value',
            'status',
            'expected_close_date',
        )
        labels = {
            'pipeline': 'Pipeline',
            'stage': 'Etapa',
            'client': 'Cliente',
            'producer': 'Produtor',
            'agent': 'Agente',
            'line_of_business': 'Ramo',
            'insurer': 'Seguradora',
            'proposal': 'Proposta',
            'title': 'Título',
            'description': 'Descrição',
            'estimated_value': 'Valor estimado',
            'status': 'Status',
            'expected_close_date': 'Data prevista de fechamento',
        }
        widgets = {
            'expected_close_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, brokerage=None, **kwargs):
        self.brokerage = brokerage
        super().__init__(*args, **kwargs)
        self.fields['pipeline'].queryset = Pipeline.objects.none()
        self.fields['stage'].queryset = Stage.objects.none()
        self.fields['stage'].required = False
        self.fields['client'].queryset = Client.objects.none()
        self.fields['producer'].queryset = Producer.objects.none()
        self.fields['agent'].queryset = Agent.objects.none()
        self.fields['line_of_business'].queryset = LineOfBusiness.objects.none()
        self.fields['insurer'].queryset = Insurer.objects.none()
        self.fields['proposal'].queryset = Proposal.objects.none()

        if brokerage is None:
            return

        self.fields['pipeline'].queryset = Pipeline.objects.filter(
            brokerage=brokerage,
        ).order_by('name')
        self.fields['stage'].queryset = Stage.objects.filter(
            brokerage=brokerage,
        ).select_related('pipeline').order_by('pipeline__name', 'order', 'id')
        self.fields['client'].queryset = Client.objects.filter(
            brokerage=brokerage,
        ).order_by('name')
        self.fields['producer'].queryset = Producer.objects.filter(
            brokerage=brokerage,
            is_active=True,
        ).order_by('name')
        self.fields['agent'].queryset = Agent.objects.filter(
            brokerage=brokerage,
            is_active=True,
        ).order_by('name')
        self.fields['line_of_business'].queryset = LineOfBusiness.objects.filter(
            brokerage=brokerage,
            is_active=True,
        ).order_by('name')
        self.fields['insurer'].queryset = Insurer.objects.filter(
            brokerage=brokerage,
            is_active=True,
        ).order_by('name')
        self.fields['proposal'].queryset = Proposal.objects.filter(
            brokerage=brokerage,
        ).order_by('-created_at')

    def clean(self):
        cleaned_data = super().clean()
        pipeline = cleaned_data.get('pipeline')
        stage = cleaned_data.get('stage')
        if stage and pipeline and stage.pipeline_id != pipeline.id:
            self.add_error(
                'stage',
                'A etapa não pertence ao pipeline informado.',
            )
        return cleaned_data


class DealSearchForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os status')] + list(Deal.Status.choices),
    )
    pipeline = forms.ModelChoiceField(
        required=False,
        queryset=Pipeline.objects.none(),
        empty_label='Todos os pipelines',
    )
    stage = forms.ModelChoiceField(
        required=False,
        queryset=Stage.objects.none(),
        empty_label='Todas as etapas',
    )
    producer = forms.ModelChoiceField(
        required=False,
        queryset=Producer.objects.none(),
        empty_label='Todos os produtores',
    )

    def __init__(self, *args, brokerage=None, **kwargs):
        super().__init__(*args, **kwargs)
        if brokerage is None:
            return
        self.fields['pipeline'].queryset = Pipeline.objects.filter(
            brokerage=brokerage,
        ).order_by('name')
        self.fields['stage'].queryset = Stage.objects.filter(
            brokerage=brokerage,
        ).order_by('pipeline__name', 'order', 'id')
        self.fields['producer'].queryset = Producer.objects.filter(
            brokerage=brokerage,
            is_active=True,
        ).order_by('name')


class MoveDealForm(forms.Form):
    target_stage_id = forms.IntegerField()
