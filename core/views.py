from django.shortcuts import redirect
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.views.generic import TemplateView


class LandingView(TemplateView):
    """Public landing at /. Authenticated users are redirected to /painel/."""

    template_name = 'landing.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('home'))
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        try:
            get_template(self.template_name)
        except TemplateDoesNotExist:
            return ['home.html']
        return [self.template_name]
