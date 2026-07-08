from django.core.management.base import BaseCommand

from crm.services import seed_default_pipeline
from tenants.models import Brokerage


class Command(BaseCommand):
    help = 'Cria pipeline padrão para brokerages existentes sem pipeline.'

    def handle(self, *args, **options):
        created = 0
        for brokerage in Brokerage.objects.all():
            pipeline = seed_default_pipeline(brokerage)
            if pipeline.stages.count() == 6:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Backfill: {created} pipelines garantidos.'
            )
        )
