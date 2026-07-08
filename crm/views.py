from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from base.mixins import RoleRequiredMixin, TenantQuerysetMixin
from crm.forms import (
    DealForm,
    DealSearchForm,
    MoveDealForm,
    PipelineForm,
    StageFormSet,
)
from crm.models import Deal, DealStageHistory, Pipeline, Stage
from crm.services import move_deal_to_stage


class PipelineListView(RoleRequiredMixin, TenantQuerysetMixin, ListView):
    template_name = 'crm/pipeline_list.html'
    model = Pipeline
    context_object_name = 'pipelines'
    allowed_roles = ('owner', 'manager')

    def get_queryset(self):
        return super().get_queryset().prefetch_related('stages')


class PipelineFormSetMixin:
    model = Pipeline
    form_class = PipelineForm
    template_name = 'crm/pipeline_form.html'
    allowed_roles = ('owner', 'manager')

    def get_success_url(self):
        return reverse_lazy('crm:pipeline_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['stage_formset'] = StageFormSet(
                self.request.POST,
                instance=getattr(self, 'object', None),
            )
        else:
            context['stage_formset'] = StageFormSet(
                instance=getattr(self, 'object', None),
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        stage_formset = context['stage_formset']
        if not stage_formset.is_valid():
            return self.form_invalid(form)
        form.instance.brokerage = self.request.tenant
        self.object = form.save()
        for deleted_object in stage_formset.deleted_objects:
            deleted_object.delete()
        stages = stage_formset.save(commit=False)
        for stage in stages:
            stage.brokerage = self.request.tenant
            stage.pipeline = self.object
            stage.save()
        stage_formset.save_m2m()
        return redirect(self.get_success_url())


class PipelineCreateView(
    RoleRequiredMixin,
    TenantQuerysetMixin,
    PipelineFormSetMixin,
    CreateView,
):
    allowed_roles = ('owner', 'manager')


class PipelineUpdateView(
    RoleRequiredMixin,
    TenantQuerysetMixin,
    PipelineFormSetMixin,
    UpdateView,
):
    allowed_roles = ('owner', 'manager')


class DealListView(RoleRequiredMixin, TenantQuerysetMixin, ListView):
    template_name = 'crm/deal_list.html'
    model = Deal
    context_object_name = 'deals'
    paginate_by = 25
    allowed_roles = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'pipeline',
            'stage',
            'client',
            'producer',
            'agent',
            'line_of_business',
            'insurer',
            'proposal',
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(client__name__icontains=query)
            )
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
        pipeline = self.request.GET.get('pipeline', '').strip()
        if pipeline:
            queryset = queryset.filter(pipeline_id=pipeline)
        stage = self.request.GET.get('stage', '').strip()
        if stage:
            queryset = queryset.filter(stage_id=stage)
        producer = self.request.GET.get('producer', '').strip()
        if producer:
            queryset = queryset.filter(producer_id=producer)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DealSearchForm(
            self.request.GET or None,
            brokerage=self.request.tenant,
        )
        context.update(
            self.get_queryset().aggregate(
                total_open_amount=Sum(
                    'estimated_value',
                    filter=Q(status=Deal.Status.OPEN),
                    default=Decimal('0'),
                ),
                total_open_count=Count(
                    'id',
                    filter=Q(status=Deal.Status.OPEN),
                ),
                total_won_amount=Sum(
                    'estimated_value',
                    filter=Q(status=Deal.Status.WON),
                    default=Decimal('0'),
                ),
                total_won_count=Count(
                    'id',
                    filter=Q(status=Deal.Status.WON),
                ),
                total_lost_amount=Sum(
                    'estimated_value',
                    filter=Q(status=Deal.Status.LOST),
                    default=Decimal('0'),
                ),
                total_lost_count=Count(
                    'id',
                    filter=Q(status=Deal.Status.LOST),
                ),
            )
        )
        return context


class DealCreateView(RoleRequiredMixin, TenantQuerysetMixin, CreateView):
    template_name = 'crm/deal_form.html'
    model = Deal
    form_class = DealForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent', 'producer')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.brokerage = self.request.tenant
        form.instance.created_by = self.request.user
        if form.instance.stage_id is None:
            form.instance.stage = form.instance.pipeline.stages.order_by(
                'order',
                'id',
            ).first()
        response = super().form_valid(form)
        DealStageHistory.objects.create(
            brokerage=self.request.tenant,
            deal=self.object,
            from_stage=None,
            to_stage=self.object.stage,
            changed_by=self.request.user,
            note='Negociação criada.',
        )
        return response

    def get_success_url(self):
        return reverse_lazy('crm:deal_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class DealUpdateView(RoleRequiredMixin, TenantQuerysetMixin, UpdateView):
    template_name = 'crm/deal_form.html'
    model = Deal
    form_class = DealForm
    allowed_roles = ('owner', 'manager', 'broker', 'agent')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['brokerage'] = self.request.tenant
        return kwargs

    def get_success_url(self):
        return reverse_lazy('crm:deal_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'update'
        return context


class DealDetailView(RoleRequiredMixin, TenantQuerysetMixin, DetailView):
    template_name = 'crm/deal_detail.html'
    model = Deal
    context_object_name = 'deal'
    allowed_roles = ()

    def get_queryset(self):
        return super().get_queryset().select_related(
            'pipeline',
            'stage',
            'client',
            'producer',
            'agent',
            'line_of_business',
            'insurer',
            'proposal',
            'created_by',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.stage_history.select_related(
            'from_stage',
            'to_stage',
            'changed_by',
        ).order_by('-changed_at')
        return context


class KanbanView(RoleRequiredMixin, TemplateView):
    template_name = 'crm/deal_kanban.html'
    allowed_roles = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        pipeline_id = self.request.GET.get('pipeline')
        pipelines = Pipeline.objects.filter(
            brokerage=tenant,
        ).order_by('name')
        if pipeline_id:
            active = pipelines.filter(pk=pipeline_id).first()
        else:
            active = pipelines.filter(is_default=True).first() or pipelines.first()
        if active:
            stages_qs = active.stages.order_by('order', 'id')
            deals_qs = Deal.objects.filter(
                brokerage=tenant,
                pipeline=active,
            ).select_related('client', 'producer', 'stage')
        else:
            stages_qs = Stage.objects.none()
            deals_qs = Deal.objects.none()
        deals_by_stage = {
            stage.id: [
                deal for deal in deals_qs
                if deal.stage_id == stage.id
            ]
            for stage in stages_qs
        }
        context.update({
            'pipelines': pipelines,
            'active_pipeline': active,
            'stages': stages_qs,
            'deals_by_stage': deals_by_stage,
        })
        return context


class DealMoveStageView(RoleRequiredMixin, View):
    allowed_roles = ('owner', 'manager', 'broker', 'agent', 'producer')
    http_method_names = ('post',)

    def post(self, request, pk):
        deal = get_object_or_404(Deal, pk=pk, brokerage=request.tenant)
        form = MoveDealForm(request.POST)
        if not form.is_valid():
            return JsonResponse(
                {'ok': False, 'error': 'target_stage_id inválido.'},
                status=400,
            )
        target_stage_id = form.cleaned_data['target_stage_id']
        target = Stage.objects.filter(
            pk=target_stage_id,
            brokerage=request.tenant,
        ).first()
        if target is None:
            return JsonResponse(
                {'ok': False, 'error': 'Etapa não encontrada.'},
                status=404,
            )
        try:
            move_deal_to_stage(
                deal=deal,
                target_stage=target,
                user=request.user,
            )
        except ValueError as error:
            return JsonResponse(
                {'ok': False, 'error': str(error)},
                status=400,
            )
        deal.refresh_from_db(fields=['stage', 'status'])
        return JsonResponse({
            'ok': True,
            'deal_id': deal.id,
            'stage_id': target.id,
            'status': deal.status,
        })
