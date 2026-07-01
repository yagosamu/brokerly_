from django.core.management.base import BaseCommand

from commissions.services import generate_commission_for_policy
from insurance.models import Policy


class Command(BaseCommand):
    help = 'Cria Commission para cada Policy existente sem comissão.'

    def handle(self, *args, **options):
        created = 0
        for policy in Policy.objects.filter(commission__isnull=True):
            generate_commission_for_policy(policy)
            created += 1
        self.stdout.write(
            self.style.SUCCESS(f'Backfill: {created} comissões criadas.')
        )
