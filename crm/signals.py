from django.db.models.signals import post_save
from django.dispatch import receiver

from tenants.models import Brokerage


@receiver(post_save, sender=Brokerage)
def seed_pipeline_for_new_brokerage(sender, instance, created, **kwargs):
    if not created:
        return
    from crm.services import seed_default_pipeline
    seed_default_pipeline(instance)
