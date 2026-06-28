from django.apps import apps
from django.db.models.signals import post_migrate
from django.dispatch import receiver


FREE_PLAN_DEFAULTS = {
    'name': 'Free',
    'price': 0,
    'max_users': 3,
    'max_clients': 50,
    'max_policies': 100,
    'features': ['Cadastro de clientes', 'Propostas e apólices', 'CRM'],
    'is_available': True,
}


@receiver(post_migrate)
def seed_free_plan(sender, **kwargs):
    if sender.label != 'tenants':
        return
    plan_model = apps.get_model('tenants', 'Plan')
    plan_model.objects.get_or_create(slug='free', defaults=FREE_PLAN_DEFAULTS)
