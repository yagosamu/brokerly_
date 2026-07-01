from django.db.models.signals import post_save
from django.dispatch import receiver

from insurance.models import Policy


@receiver(post_save, sender=Policy)
def create_commission_for_new_policy(sender, instance, created, **kwargs):
    if not created:
        return
    from commissions.services import generate_commission_for_policy

    generate_commission_for_policy(instance)
