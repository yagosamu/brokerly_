from django.contrib.auth.mixins import LoginRequiredMixin
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView

from dashboard.services import (
    _period_range,
    claims_by_status,
    funnel_data,
    kpi_counters,
    monthly_premium_series,
    policies_by_line,
    rule_based_insights,
    top_insurers,
    top_producers,
    upcoming_renewals,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_template_names(self):
        try:
            get_template(self.template_name)
        except TemplateDoesNotExist:
            return ['home.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = getattr(self.request, 'tenant', None)
        period = self.request.GET.get('period', '30d')
        date_from = parse_date(self.request.GET.get('date_from', '') or '')
        date_to = parse_date(self.request.GET.get('date_to', '') or '')
        start, end = _period_range(period, date_from, date_to)

        if tenant is None:
            context.update({
                'no_tenant': True,
                'period': period,
                'date_from': date_from,
                'date_to': date_to,
                'start': start,
                'end': end,
            })
            return context

        kpis = kpi_counters(tenant, start, end)
        funnel = funnel_data(tenant)
        renewals = upcoming_renewals(tenant, limit=5, horizon_days=90)
        context.update({
            'no_tenant': False,
            'period': period,
            'date_from': date_from,
            'date_to': date_to,
            'start': start,
            'end': end,
            'kpis': kpis,
            'funnel': funnel,
            'monthly_series': monthly_premium_series(tenant, months=12),
            'policies_by_line': policies_by_line(tenant, start, end),
            'claims_status': claims_by_status(tenant, start, end),
            'top_insurers': top_insurers(tenant),
            'top_producers': top_producers(tenant),
            'upcoming_renewals': renewals,
            'insights': rule_based_insights(tenant, kpis, funnel, renewals[:1]),
        })
        return context
